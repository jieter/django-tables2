# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.core.handlers.wsgi import WSGIRequest
from django.utils.functional import curry
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.test.client import FakePayload
from itertools import chain, ifilter
import inspect
from StringIO import StringIO
import warnings


class Sequence(list):
    """
    Represents a column sequence, e.g. ``("first_name", "...", "last_name")``

    This is used to represent `.Table.Meta.sequence` or the `.Table`
    constructors's *sequence* keyword argument.

    The sequence must be a list of column names and is used to specify the
    order of the columns on a table. Optionally a "..." item can be inserted,
    which is treated as a *catch-all* for column names that aren't explicitly
    specified.
    """
    def expand(self, columns):
        """
        Expands the ``"..."`` item in the sequence into the appropriate column
        names that should be placed there.

        :raises: `ValueError` if the sequence is invalid for the columns.
        """
        ellipses = self.count("...")
        if ellipses > 1:
            raise ValueError("'...' must be used at most once in a sequence.")
        elif ellipses == 0:
            self.append("...")

        # everything looks good, let's expand the "..." item
        columns = columns[:]  # don't modify
        head = []
        tail = []
        target = head  # start by adding things to the head
        for name in self:
            if name == "...":
                # now we'll start adding elements to the tail
                target = tail
                continue
            target.append(name)
            if name in columns:
                columns.pop(columns.index(name))
        self[:] = chain(head, columns, tail)


class OrderBy(str):
    """
    A single item in an `.OrderByTuple` object. This class is
    essentially just a `str` with some extra properties.
    """
    @property
    def bare(self):
        """
        Return the bare form.

        The *bare form* is the non-prefixed form. Typically the bare form is
        just the ascending form.

        Example: ``age`` is the bare form of ``-age``

        :rtype: `.OrderBy` object
        """
        return OrderBy(self[1:]) if self[:1] == '-' else self

    @property
    def opposite(self):
        """
        Return an `.OrderBy` object with an opposite sort influence.

        Example:

        .. code-block:: python

            >>> order_by = OrderBy('name')
            >>> order_by.opposite
            '-name'

        :rtype: `.OrderBy` object
        """
        return OrderBy(self[1:]) if self.is_descending else OrderBy('-' + self)

    @property
    def is_descending(self):
        """
        Return `True` if this object induces *descending* ordering

        :rtype: `bool`
        """
        return self.startswith('-')

    @property
    def is_ascending(self):
        """
        Return `True` if this object induces *ascending* ordering.

        :returns: `bool`
        """
        return not self.is_descending


class OrderByTuple(tuple):
    """Stores ordering as (as `.OrderBy` objects). The
    `~django_tables2.tables.Table.order_by` property is always converted
    to an `.OrderByTuple` object.

    This class is essentially just a `tuple` with some useful extras.

    Example:

    .. code-block:: python

        >>> x = OrderByTuple(('name', '-age'))
        >>> x['age']
        '-age'
        >>> x['age'].is_descending
        True
        >>> x['age'].opposite
        'age'

    """
    def __new__(cls, iterable):
        transformed = []
        for item in iterable:
            if not isinstance(item, OrderBy):
                item = OrderBy(item)
            transformed.append(item)
        return super(OrderByTuple, cls).__new__(cls, transformed)

    def __unicode__(self):
        """Human readable format."""
        return ','.join(self)

    def __str__(self):
        return unicode(self).encode('utf-8')

    def __contains__(self, name):
        """
        Determine if a column has an influence on ordering.

        Example:

        .. code-block:: python

            >>> ordering =
            >>> x = OrderByTuple(('name', ))
            >>> 'name' in  x
            True
            >>> '-name' in x
            True

        :param name: The name of a column. (optionally prefixed)
        :returns: `bool`
        """
        name = OrderBy(name).bare
        for order_by in self:
            if order_by.bare == name:
                return True
        return False

    def __getitem__(self, index):
        """
        Allows an `.OrderBy` object to be extracted via named or integer
        based indexing.

        When using named based indexing, it's fine to used a prefixed named.

        .. code-block:: python

            >>> x = OrderByTuple(('name', '-age'))
            >>> x[0]
            'name'
            >>> x['age']
            '-age'
            >>> x['-age']
            '-age'

        :rtype: `.OrderBy` object
        """
        if isinstance(index, basestring):
            for order_by in self:
                if order_by == index or order_by.bare == index:
                    return order_by
            raise KeyError
        return super(OrderByTuple, self).__getitem__(index)

    @property
    def cmp(self):
        """
        Return a function for use with `list.sort` that implements this
        object's ordering. This is used to sort non-`.QuerySet` based
        :term:`table data`.

        :rtype: function
        """
        # pylint: disable=C0103
        def _cmp(a, b):
            for accessor, reverse in instructions:
                x = accessor.resolve(a)
                y = accessor.resolve(b)
                try:
                    res = cmp(x, y)
                except TypeError:
                    res = cmp((repr(type(x)), id(type(x)), x),
                              (repr(type(y)), id(type(y)), y))
                if res != 0:
                    return -res if reverse else res
            return 0
        instructions = []
        for order_by in self:
            if order_by.startswith('-'):
                instructions.append((Accessor(order_by[1:]), True))
            else:
                instructions.append((Accessor(order_by), False))
        return _cmp

    def get(self, key, fallback):
        """
        Identical to __getitem__, but supports fallback value.
        """
        try:
            return self[key]
        except (KeyError, IndexError):
            return fallback

    @property
    def opposite(self):
        """
        Return version with each `.OrderBy` prefix toggled.

        Example:

        .. code-block:: python

            >>> order_by = OrderByTuple(('name', '-age'))
            >>> order_by.opposite
            ('-name', 'age')
        """
        return type(self)((o.opposite for o in self))


class Accessor(str):
    """
    A string describing a path from one object to another via attribute/index
    accesses. For convenience, the class has an alias `.A` to allow for more concise code.

    Relations are separated by a ``.`` character.
    """
    SEPARATOR = '.'

    def resolve(self, context, safe=True, quiet=False):
        """
        Return an object described by the accessor by traversing the attributes
        of *context*.

        Example:

        .. code-block:: python

            >>> x = Accessor('__len__')
            >>> x.resolve('brad')
            4
            >>> x = Accessor('0.upper')
            >>> x.resolve('brad')
            'B'

        :type  context: `object`
        :param context: The root/first object to traverse.
        :type     safe: `bool`
        :param    safe: Don't call anything with ``alters_data = True``
        :type    quiet: bool
        :param   quiet: Smother all exceptions and instead return `None`
        :returns: target object
        :raises: anything ``getattr(a, "b")`` raises, e.g. `TypeError`,
                 `AttributeError`, `KeyError`, `ValueError` (unless *quiet* ==
                 `True`)

        `~.Accessor.resolve` attempts lookups in the following order:

        - dictionary (e.g. ``obj[related]``)
        - attribute (e.g. ``obj.related``)
        - list-index lookup (e.g. ``obj[int(related)]``)

        Callable objects are called, and their result is used, before
        proceeding with the resolving.
        """
        try:
            current = context
            for bit in self.bits:
                try:  # dictionary lookup
                    current = current[bit]
                except (TypeError, AttributeError, KeyError):
                    try:  # attribute lookup
                        current = getattr(current, bit)
                    except (TypeError, AttributeError):
                        try:  # list-index lookup
                            current = current[int(bit)]
                        except (IndexError,  # list index out of range
                                ValueError,  # invalid literal for int()
                                KeyError,    # dict without `int(bit)` key
                                TypeError,   # unsubscriptable object
                                ):
                            raise ValueError('Failed lookup for key [%s] in %r'
                                             ', when resolving the accessor %s'
                                              % (bit, current, self))
                if callable(current):
                    if safe and getattr(current, 'alters_data', False):
                        raise ValueError('refusing to call %s() because `.alters_data = True`'
                                         % repr(current))
                    current = current()
                # important that we break in None case, or a relationship
                # spanning across a null-key will raise an exception in the
                # next iteration, instead of defaulting.
                if current is None:
                    break
            return current
        except:
            if not quiet:
                raise

    @property
    def bits(self):
        if self == '':
            return ()
        return self.split(self.SEPARATOR)


A = Accessor  # alias

class AttributeDict(dict):
    """
    A wrapper around `dict` that knows how to render itself as HTML
    style tag attributes.

    The returned string is marked safe, so it can be used safely in a template.
    See `.as_html` for a usage example.
    """
    def as_html(self):
        """
        Render to HTML tag attributes.

        Example:

        .. code-block:: python

            >>> from django_tables2.utils import AttributeDict
            >>> attrs = AttributeDict({'class': 'mytable', 'id': 'someid'})
            >>> attrs.as_html()
            'class="mytable" id="someid"'

        :rtype: `~django.utils.safestring.SafeUnicode` object

        """
        return mark_safe(' '.join(['%s="%s"' % (k, escape(v))
                                   for k, v in self.iteritems()]))


class Attrs(dict):
    """
    Backwards compatibility, deprecated.
    """
    def __init__(self, *args, **kwargs):
        super(Attrs, self).__init__(*args, **kwargs)
        warnings.warn("Attrs class is deprecated, use dict instead.",
                      DeprecationWarning)


def segment(sequence, aliases):
    """
    Translates a flat sequence of items into a set of prefixed aliases.

    This allows the value set by `.QuerySet.order_by` to be translated into
    a list of columns that would have the same result. These are called
    "order by aliases" which are optionally prefixed column names.

    e.g.

        >>> list(segment(("a", "-b", "c"),
        ...              {"x": ("a"),
        ...               "y": ("b", "-c"),
        ...               "z": ("-b", "c")}))
        [["x", "-y"], ["x", "z"]]

    """
    if not (sequence or aliases):
        return
    for alias, parts in aliases.items():
        variants = {
            # alias: order by tuple
            alias:  OrderByTuple(parts),
            OrderBy(alias).opposite: OrderByTuple(parts).opposite,
        }
        for valias, vparts in variants.items():
            if list(sequence[:len(vparts)]) == list(vparts):
                tail_aliases = dict(aliases)
                del tail_aliases[alias]
                tail_sequence = sequence[len(vparts):]
                if tail_sequence:
                    for tail in segment(tail_sequence, tail_aliases):
                        yield [valias] + tail
                    else:
                        continue
                else:
                    yield [valias]


class cached_property(object):  # pylint: disable=C0103
    """
    Decorator that creates converts a method with a single
    self argument into a property cached on the instance.

    Taken directly from Django 1.4.
    """
    def __init__(self, func):
        from functools import wraps
        wraps(func)(self)
        self.func = func

    def __get__(self, instance, cls):
        res = instance.__dict__[self.func.__name__] = self.func(instance)
        return res


funcs = ifilter(curry(hasattr, inspect), ('getfullargspec', 'getargspec'))
getargspec = getattr(inspect, next(funcs))
del funcs


def build_request(uri='/'):
    """
    Return a fresh HTTP GET / request.

    This is essentially a heavily cutdown version of Django 1.3's
    `~django.test.client.RequestFactory`.
    """
    path, _, querystring = uri.partition('?')
    return WSGIRequest({
            'CONTENT_TYPE':      'text/html; charset=utf-8',
            'PATH_INFO':         path,
            'QUERY_STRING':      querystring,
            'REMOTE_ADDR':       '127.0.0.1',
            'REQUEST_METHOD':    'GET',
            'SCRIPT_NAME':       '',
            'SERVER_NAME':       'testserver',
            'SERVER_PORT':       '80',
            'SERVER_PROTOCOL':   'HTTP/1.1',
            'wsgi.version':      (1, 0),
            'wsgi.url_scheme':   'http',
            'wsgi.input':        FakePayload(b''),
            'wsgi.errors':       StringIO(),
            'wsgi.multiprocess': True,
            'wsgi.multithread':  False,
            'wsgi.run_once':     False,
        })


# helper context managers to support older Djangos
# for testing purposes only. borrowed from Django 1.4 with some modifications

from django.conf import settings
from django.conf import UserSettingsHolder
from django.utils import translation


class override_settings(object):
    """
    Acts as either a decorator, or a context manager. If it's a decorator it
    takes a function and returns a wrapped function. If it's a contextmanager
    it's used with the ``with`` statement. In either event entering/exiting
    are called before and after, respectively, the function/block is executed.
    """
    def __init__(self, **kwargs):
        self.options = kwargs
        self.wrapped = settings._wrapped

    def __enter__(self):
        self.enable()

    def __exit__(self, exc_type, exc_value, traceback):
        self.disable()

    # we don't need __call__ since we're using this as a contextmanager only

    def enable(self):
        override = UserSettingsHolder(settings._wrapped)
        for key, new_value in self.options.items():
            setattr(override, key, new_value)
        settings._wrapped = override
        # we dont need to send signal "setting_changed"

    def disable(self):
        settings._wrapped = self.wrapped
        # we dont need to send signal "setting_changed"


class override_translation(object):
    def __init__(self, language, deactivate=False):
        self.language = language
        self.deactivate = deactivate
        self.old_language = translation.get_language()

    def __enter__(self):
        if self.language is not None:
            translation.activate(self.language)
        else:
            translation.deactivate_all()

    def __exit__(self, exc_type, exc_value, traceback):
        if self.deactivate:
            translation.deactivate()
        else:
            translation.activate(self.old_language)
