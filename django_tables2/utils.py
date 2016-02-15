# coding: utf-8
from __future__ import absolute_import, unicode_literals

import inspect
from functools import total_ordering
from itertools import chain

import six
from django import VERSION as django_version
from django.db.models.fields import FieldDoesNotExist
from django.utils.html import escape
from django.utils.safestring import mark_safe


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


@six.python_2_unicode_compatible
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

    def __str__(self):
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
                                             ', when resolving the accessor %s' % (bit, current, self)
                                             )
                if callable(current):
                    if safe and getattr(current, 'alters_data', False):
                        raise ValueError('refusing to call %s() because `.alters_data = True`'
                                         % repr(current))
                    if not getattr(current, 'do_not_call_in_templates', False):
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

    def get_field(self, model, quiet=False):
        '''Return the django model field for model in context, following relations'''
        if not hasattr(model, '_meta'):
            return

        field = None
        for bit in self.bits:
            try:
                if django_version < (1, 8):
                    # remove if support for django 1.7 is dropped.
                    field, _, _, _ = model._meta.get_field_by_name(bit)
                else:
                    field = model._meta.get_field(bit)
            except FieldDoesNotExist:
                break
            if hasattr(field, 'rel') and hasattr(field.rel, 'to'):
                model = field.rel.to
                continue

        return field


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
        return mark_safe(' '.join(['%s="%s"' % (k, escape(v if not callable(v) else v()))
                                   for k, v in six.iteritems(self)]))


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
        [("x", "-y"), ("x", "z")]

    """
    if not (sequence or aliases):
        return
    for alias, parts in aliases.items():
        variants = {
            # alias: order by tuple
            alias: OrderByTuple(parts),
            OrderBy(alias).opposite: OrderByTuple(parts).opposite,
        }
        for valias, vparts in variants.items():
            if list(sequence[:len(vparts)]) == list(vparts):
                tail_aliases = dict(aliases)
                del tail_aliases[alias]
                tail_sequence = sequence[len(vparts):]
                if tail_sequence:
                    for tail in segment(tail_sequence, tail_aliases):
                        yield tuple(chain([valias], tail))
                    else:
                        continue
                else:
                    yield tuple([valias])


funcs = (name for name in ('getfullargspec', 'getargspec') if hasattr(inspect, name))
getargspec = getattr(inspect, next(funcs))
del funcs


def computed_values(d):
    """
    Computes a new `dict` that has callable values replaced with the return values.

    Simple example:

        >>> compute_values({"foo": lambda: "bar"})
        {"foo": "bar"}

    Arbitrarily deep structures are supported. The logic is as follows:

    1. If the value is callable, call it and make that the new value.
    2. If the value is an instance of dict, use ComputableDict to compute its keys.

    Example:

        >>> def parents():
        ...     return {
        ...         "father": lambda: "Foo",
        ...         "mother": "Bar"
        ...      }
        ...
        >>> a = {
        ...     "name": "Brad",
        ...     "parents": parents
        ... }
        ...
        >>> computed_values(a)
        {"name": "Brad", "parents": {"father": "Foo", "mother": "Bar"}}

    :rtype: dict
    """
    result = {}
    for k, v in six.iteritems(d):
        if callable(v):
            v = v()
        if isinstance(v, dict):
            v = computed_values(v)
        result[k] = v
    return result


def has_callable_attr(obj, attr_name):
    attr = getattr(obj, attr_name, None)
    if callable(attr):
        return True
    else:
        return False


def get_model_meta_field(model, part):
    """
    compatible across django 1.8
    """
    if django_version < (1, 8, 0):
        field, _, _, _ = model._meta.get_field_by_name(part)
    else:
        field = model._meta.get_field(part)

    return field
