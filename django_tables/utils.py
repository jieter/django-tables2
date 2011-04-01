# -*- coding: utf-8 -*-
from django.utils.datastructures import SortedDict
from django.template import Context
from django.utils.encoding import force_unicode, StrAndUnicode
from django.utils.safestring import mark_safe
from django.template.defaultfilters import escape


__all__ = ('BaseTable', 'options')


class OrderBy(str):
    """A single element in an :class:`OrderByTuple`. This class is essentially
    just a :class:`str` with some extra properties.

    """
    @property
    def bare(self):
        """Return the bare or naked version. That is, remove a ``-`` prefix if
        it exists and return the result.

        """
        return OrderBy(self[1:]) if self[:1] == '-' else self

    @property
    def opposite(self):
        """Return the an :class:`OrderBy` object with the opposite sort
        influence. e.g.

        .. code-block:: python

            >>> order_by = OrderBy('name')
            >>> order_by.opposite
            '-name'

        """
        return OrderBy(self[1:]) if self.is_descending else OrderBy('-' + self)

    @property
    def is_descending(self):
        """Return :const:`True` if this object induces *descending* ordering."""
        return self.startswith('-')

    @property
    def is_ascending(self):
        """Return :const:`True` if this object induces *ascending* ordering."""
        return not self.is_descending


class OrderByTuple(tuple, StrAndUnicode):
    """Stores ordering instructions (as :class:`OrderBy` objects). The
    :attr:`Table.order_by` property is always converted into an
    :class:`OrderByTuplw` objectUsed to render output in a format we understand
    as input (see :meth:`~OrderByTuple.__unicode__`) - especially useful in
    templates.

    It's quite easy to create one of these. Pass in an iterable, and it will
    automatically convert each element into an :class:`OrderBy` object. e.g.

    .. code-block:: python

        >>> ordering = ('name', '-age')
        >>> order_by_tuple = OrderByTuple(ordering)
        >>> age = order_by_tuple['age']
        >>> age
        '-age'
        >>> age.is_descending
        True
        >>> age.opposite
        'age'

    """
    def __new__(cls, iterable):
        transformed = []
        for item in iterable:
            if not isinstance(item, OrderBy):
                item = OrderBy(item)
            transformed.append(item)
        return tuple.__new__(cls, transformed)

    def __unicode__(self):
        """Output in human readable format."""
        return ','.join(self)

    def __contains__(self, name):
        """Determine whether a column is part of this order (i.e. descending
        prefix agnostic). e.g.

        .. code-block:: python

            >>> ordering = ('name', '-age')
            >>> order_by_tuple = OrderByTuple(ordering)
            >>> 'age' in  order_by_tuple
            True
            >>> '-age' in order_by_tuple
            True

        """
        for o in self:
            if o == name or o.bare == name:
                return True
        return False

    def __getitem__(self, index):
        """Allows an :class:`OrderBy` object to be extracted using
        :class:`dict`-style indexing in addition to standard 0-based integer
        indexing. The :class:`dict`-style is prefix agnostic in the same way as
        :meth:`~OrderByTuple.__contains__`.

        .. code-block:: python

            >>> ordering = ('name', '-age')
            >>> order_by_tuple = OrderByTuple(ordering)
            >>> order_by_tuple['age']
            '-age'
            >>> order_by_tuple['-age']
            '-age'

        """
        if isinstance(index, basestring):
            for ob in self:
                if ob == index or ob.bare == index:
                    return ob
            raise IndexError
        return tuple.__getitem__(self, index)

    @property
    def cmp(self):
        """Return a function suitable for sorting a list. This is used for
        non-:class:`QuerySet` data sources.

        """
        def _cmp(a, b):
            for accessor, reverse in instructions:
                res = cmp(accessor.resolve(a), accessor.resolve(b))
                if res != 0:
                    return -res if reverse else res
            return 0
        instructions = []
        for o in self:
            if o.startswith('-'):
                instructions.append((Accessor(o[1:]), True))
            else:
                instructions.append((Accessor(o), False))
        return _cmp


class Accessor(str):
    SEPARATOR = '.'

    def resolve(self, context):
        # Try to resolve relationships spanning attributes. This is
        # basically a copy/paste from django/template/base.py in
        # Variable._resolve_lookup()
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
                    except (IndexError, # list index out of range
                            ValueError, # invalid literal for int()
                            KeyError,   # dict without `int(bit)` key
                            TypeError,  # unsubscriptable object
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
        return self.split(self.SEPARATOR)


A = Accessor  # alias

class AttributeDict(dict):
    """A wrapper around :class:`dict` that knows how to render itself as HTML
    style tag attributes.

    """
    def as_html(self):
        """Render as HTML style tag attributes."""
        return mark_safe(' '.join(['%s="%s"' % (k, escape(v))
                                   for k, v in self.iteritems()]))
