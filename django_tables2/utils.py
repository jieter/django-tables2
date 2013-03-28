# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.core.handlers.wsgi import WSGIRequest
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.test.client import FakePayload
from itertools import chain
import inspect
import operator
import six
import warnings


def python_2_unicode_compatible(klass):
    """
    A decorator that defines __unicode__ and __str__ methods under Python 2.
    Under Python 3 it does nothing.

    To support Python 2 and 3 with a single code base, define a __str__ method
    returning text and apply this decorator to the class.

    Taken directly from Django.
    """
    if not six.PY3:
        klass.__unicode__ = klass.__str__
        klass.__str__ = lambda self: self.__unicode__().encode('utf-8')
    return klass


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
        columns = list(columns)  # take a copy and exhaust the generator
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


class OrderBy(six.text_type):
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


@python_2_unicode_compatible
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
        return ','.join(self)

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
        if isinstance(index, six.string_types):
            for order_by in self:
                if order_by == index or order_by.bare == index:
                    return order_by
            raise KeyError
        return super(OrderByTuple, self).__getitem__(index)

    @property
    def key(self):
        accessors = []
        reversing = []
        for order_by in self:
            accessors.append(Accessor(order_by.bare))
            reversing.append(order_by.is_descending)

        @total_ordering
        class Comparator(object):
            def __init__(self, obj):
                self.obj = obj

            def __eq__(self, other):
                for accessor in accessors:
                    a = accessor.resolve(self.obj, quiet=True)
                    b = accessor.resolve(other.obj, quiet=True)
                    if not a == b:
                        return False
                return True

            def __lt__(self, other):
                for accessor, reverse in six.moves.zip(accessors, reversing):
                    a = accessor.resolve(self.obj, quiet=True)
                    b = accessor.resolve(other.obj, quiet=True)
                    if a == b:
                        continue
                    if reverse:
                        a, b = b, a
                    # The rest of this should be refactored out into a util
                    # function 'compare' that handles different types.
                    try:
                        return a < b
                    except TypeError:
                        # If the truth values differ, it's a good way to
                        # determine ordering.
                        if bool(a) is not bool(b):
                            return bool(a) < bool(b)
                        # Handle comparing different types, by falling back to
                        # the string and id of the type. This at least groups
                        # different types together.
                        a_type = type(a)
                        b_type = type(b)
                        return (repr(a_type), id(a_type)) < (repr(b_type), id(b_type))
                return False
        return Comparator

    @property
    def cmp(self):
        """
        Return a function for use with `list.sort` that implements this
        object's ordering. This is used to sort non-`.QuerySet` based
        :term:`table data`.

        :rtype: function
        """
        warnings.warn('`cmp` is deprecated, use `key` instead.',
                      DeprecationWarning)

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
                                   for k, v in six.iteritems(self)]))


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


funcs = (name for name in ('getfullargspec', 'getargspec')
                       if hasattr(inspect, name))
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
        'wsgi.errors':       six.StringIO(),
        'wsgi.multiprocess': True,
        'wsgi.multithread':  False,
        'wsgi.run_once':     False,
    })


def total_ordering(cls):
    """Class decorator that fills in missing ordering methods"""
    convert = {
        '__lt__': [('__gt__', lambda self, other: not (self < other or self == other)),
                   ('__le__', lambda self, other: self < other or self == other),
                   ('__ge__', lambda self, other: not self < other)],
        '__le__': [('__ge__', lambda self, other: not self <= other or self == other),
                   ('__lt__', lambda self, other: self <= other and not self == other),
                   ('__gt__', lambda self, other: not self <= other)],
        '__gt__': [('__lt__', lambda self, other: not (self > other or self == other)),
                   ('__ge__', lambda self, other: self > other or self == other),
                   ('__le__', lambda self, other: not self > other)],
        '__ge__': [('__le__', lambda self, other: (not self >= other) or self == other),
                   ('__gt__', lambda self, other: self >= other and not self == other),
                   ('__lt__', lambda self, other: not self >= other)]
    }
    roots = set(dir(cls)) & set(convert)
    if not roots:
        raise ValueError('must define at least one ordering operation: < > <= >=')
    root = max(roots)       # prefer __lt__ to __le__ to __gt__ to __ge__
    for opname, opfunc in convert[root]:
        if opname not in roots:
            opfunc.__name__ = str(opname)  # Py2 requires non-unicode, Py3 requires unicode.
            opfunc.__doc__ = getattr(int, opname).__doc__
            setattr(cls, opname, opfunc)
    return cls
