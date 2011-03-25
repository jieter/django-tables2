# -*- coding: utf-8 -*-
from django.utils.datastructures import SortedDict
from django.template import Context
from django.utils.encoding import force_unicode, StrAndUnicode
from django.utils.safestring import mark_safe
from django.template.defaultfilters import escape


__all__ = ('BaseTable', 'options')


def rmprefix(s):
    """Normalize a column name by removing a potential sort prefix"""
    return s[1:] if s[:1] == '-' else s


def toggleprefix(s):
    """Remove - prefix is existing, or add if missing."""
    return s[1:] if s[:1] == '-' else '-' + s


class OrderByTuple(tuple, StrAndUnicode):
    """Stores 'order by' instructions; Used to render output in a format we
    understand as input (see __unicode__) - especially useful in templates.

    Also supports some functionality to interact with and modify the order.
    """
    def __unicode__(self):
        """Output in our input format."""
        return ','.join(self)

    def __contains__(self, name):
        """Determine whether a column is part of this order."""
        for o in self:
            if rmprefix(o) == name:
                return True
        return False

    def is_reversed(self, name):
        """Returns a bool indicating whether the column is ordered reversed,
        None if it is missing.
        """
        for o in self:
            if o == '-' + name:
                return True
        return False

    def is_straight(self, name):
        """The opposite of is_reversed."""
        for o in self:
            if o == name:
                return True
        return False

    def polarize(self, reverse, names=()):
        """Return a new tuple with the columns from ``names`` set to "reversed"
        (e.g. prefixed with a '-'). Note that the name is ambiguous - do not
        confuse this with ``toggle()``.

        If names is not specified, all columns are reversed. If a column name
        is given that is currently not part of the order, it is added.
        """
        prefix = '-' if reverse else ''
        return OrderByTuple(
            [o if (names and rmprefix(o) not in names)
               else prefix + rmprefix(o) for o in self] +
               [prefix + name for name in names if not name in self]
        )

    def toggle(self, names=()):
        """Return a new tuple with the columns from ``names`` toggled with
        respect to their "reversed" state. E.g. a '-' prefix will be removed is
        existing, or added if lacking. Do not confuse with ``reverse()``.

        If names is not specified, all columns are toggled. If a column name is
        given that is currently not part of the order, it is added in
        non-reverse form.
        """
        return OrderByTuple(
            [o if (names and rmprefix(o) not in names)
               else (o[1:] if o[:1] == '-' else '-' + o) for o in self] +
               [name for name in names if not name in self]
        )

    @property
    def cmp(self):
        """Return a function suitable for sorting a list"""
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


class Accessor(object):
    SEPARATOR = '.'

    def __init__(self, path):
        self.path = path

    def resolve(self, context):
        if callable(self.path):
            return self.path(context)
        else:
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
                                              % (bit, current, self.path))
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
        return self.path.split(self.SEPARATOR)


class AttributeDict(dict):
    """A wrapper around :class:`dict` that knows how to render itself as HTML
    style tag attributes.

    """
    def as_html(self):
        """Render as HTML style tag attributes."""
        return mark_safe(' '.join(['%s="%s"' % (k, escape(v))
                                   for k, v in self.iteritems()]))
