# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals
from django.utils.html import escape
from django.utils.safestring import mark_safe
from itertools import chain


class Sequence(list):
    """
    Represents a column sequence, e.g. ("first_name", "...", "last_name")

    This is used to represent ``Table.Meta.sequence`` or the Table
    constructors's ``sequence`` keyword argument.

    The sequence must be a list of column names and is used to specify the
    order of the columns on a table. Optionally a "..." item can be inserted,
    which is treated as a *catch-all* for column names that aren't explicitly
    specified.
    """
    def expand(self, columns):
        """
        Expands the "..." item in the sequence into the appropriate column
        names that should be placed there.

        :raises: ``ValueError`` if the sequence is invalid for the columns.
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
    A single item in an :class:`.OrderByTuple` object. This class is
    essentially just a :class:`str` with some extra properties.
    """
    @property
    def bare(self):
        """
        Return the bare form.

        The *bare form* is the non-prefixed form. Typically the bare form is
        just the ascending form.

        Example: ``age`` is the bare form of ``-age``

        :rtype: :class:`.OrderBy` object
        """
        return OrderBy(self[1:]) if self[:1] == '-' else self

    @property
    def opposite(self):
        """
        Return an :class:`.OrderBy` object with an opposite sort influence.

        Example:

        .. code-block:: python

            >>> order_by = OrderBy('name')
            >>> order_by.opposite
            '-name'

        :rtype: :class:`.OrderBy` object
        """
        return OrderBy(self[1:]) if self.is_descending else OrderBy('-' + self)

    @property
    def is_descending(self):
        """
        Return :const:`True` if this object induces *descending* ordering

        :rtype: :class:`bool`
        """
        return self.startswith('-')

    @property
    def is_ascending(self):
        """
        Return :const:`True` if this object induces *ascending* ordering.

        :returns: :class:`bool`
        """
        return not self.is_descending


class OrderByTuple(tuple):
    """Stores ordering as (as :class:`.OrderBy` objects). The
    :attr:`django_tables2.tables.Table.order_by` property is always converted
    to an :class:`.OrderByTuple` object.

    This class is essentially just a :class:`tuple` with some useful extras.

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
        :returns: :class:`bool`
        """
        name = OrderBy(name).bare
        for order_by in self:
            if order_by.bare == name:
                return True
        return False

    def __getitem__(self, index):
        """
        Allows an :class:`.OrderBy` object to be extracted via named or integer
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

        :rtype: :class:`.OrderBy` object
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
        Return a function for use with :meth:`list.sort()` that implements this
        object's ordering. This is used to sort non-:class:`QuerySet` based
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
        Return version with each :class:`OrderBy` prefix toggled.

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
    accesses. For convenience, the class has an alias ``A`` to allow for more concise code.

    Relations are separated by a ``.`` character.
    """
    SEPARATOR = '.'

    def resolve(self, context):
        """
        Return an object described by the accessor by traversing the attributes
        of *context*.

        Example:

        .. code-block:: python

            >>> x = Accessor('__len__`')
            >>> x.resolve('brad')
            4
            >>> x = Accessor('0.upper')
            >>> x.resolve('brad')
            'B'

        :type context: :class:`object`
        :param context: The root/first object to traverse.
        :returns: target object
        :raises: TypeError, AttributeError, KeyError, ValueError

        :meth:`~.Accessor.resolve` attempts lookups in the following order:

        - dictionary (e.g. ``obj[related]``)
        - attribute (e.g. ``obj.related``)
        - list-index lookup (e.g. ``obj[int(related)]``)

        Callable objects are called, and their result is used, before
        proceeding with the resolving.
        """
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
                current = current()
            # important that we break in None case, or a relationship
            # spanning across a null-key will raise an exception in the
            # next iteration, instead of defaulting.
            if current is None:
                break
        return current

    @property
    def bits(self):
        if self == '':
            return ()
        return self.split(self.SEPARATOR)


A = Accessor  # alias

class AttributeDict(dict):
    """
    A wrapper around :class:`dict` that knows how to render itself as HTML
    style tag attributes.

    The returned string is marked safe, so it can be used safely in a template.
    See :meth:`.as_html` for a usage example.
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

        :rtype: :class:`~django.utils.safestring.SafeUnicode` object

        """
        return mark_safe(' '.join(['%s="%s"' % (k, escape(v))
                                   for k, v in self.iteritems()]))


class Attrs(dict):
    """
    A collection of :class:`AttributeDict`, each given a key.

    This class is used as a container to hold differenct sets of attributes for
    a given column. Keys indicate where the attributes should be used, and
    support varies depending on the column.

    It's used in favour of a standard `dict` to enable backwards compatibility.
    Before it was introduced, columns had an `attrs` parameter that would be
    given a `dict` and would assign it to a single (typically input) element.
    The new approach allows attributes to be specified for multiple elements.
    By using the `Attrs` class your intention to use the new mechanism is
    explicit.
    """
