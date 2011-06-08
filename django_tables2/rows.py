# -*- coding: utf-8 -*-
from itertools import imap, ifilter
import inspect
from django.utils.safestring import EscapeUnicode, SafeData
from django.utils.functional import curry


class BoundRow(object):
    """
    Represents a *specific* row in a table.

    :class:`.BoundRow` objects are a container that make it easy to access the
    final 'rendered' values for cells in a row. You can simply iterate over a
    :class:`.BoundRow` object and it will take care to return values rendered
    using the correct method (e.g. :meth:`.Column.render_FOO`)

    To access the rendered value of each cell in a row, just iterate over it:

    .. code-block:: python

        >>> import django_tables2 as tables
        >>> class SimpleTable(tables.Table):
        ...     a = tables.Column()
        ...     b = tables.CheckBoxColumn(attrs={'name': 'my_chkbox'})
        ...
        >>> table = SimpleTable([{'a': 1, 'b': 2}])
        >>> row = table.rows[0]  # we only have one row, so let's use it
        >>> for cell in row:
        ...     print cell
        ...
        1
        <input type="checkbox" name="my_chkbox" value="2" />

    Alternatively you can treat it like a list and use indexing to retrieve a
    specific cell. It should be noted that this will raise an IndexError on
    failure.

    .. code-block:: python

        >>> row[0]
        1
        >>> row[1]
        u'<input type="checkbox" name="my_chkbox" value="2" />'
        >>> row[2]
        ...
        IndexError: list index out of range

    Finally you can also treat it like a dictionary and use column names as the
    keys. This will raise KeyError on failure (unlike the above indexing using
    integers).

    .. code-block:: python

        >>> row['a']
        1
        >>> row['b']
        u'<input type="checkbox" name="my_chkbox" value="2" />'
        >>> row['c']
        ...
        KeyError: 'c'

    :param table: is the :class:`Table` in which this row exists.
    :param record: a single record from the :term:`table data` that is used to
        populate the row. A record could be a :class:`Model` object, a
        :class:`dict`, or something else.

    """
    def __init__(self, table, record):
        self._table = table
        self._record = record

    @property
    def table(self):
        """The associated :class:`.Table` object."""
        return self._table

    @property
    def record(self):
        """
        The data record from the data source which is used to populate this row
        with data.

        """
        return self._record

    def __iter__(self):
        """
        Iterate over the rendered values for cells in the row.

        Under the hood this method just makes a call to
        :meth:`.BoundRow.__getitem__` for each cell.

        """
        for column in self.table.columns:
            # this uses __getitem__, using the name (rather than the accessor)
            # is correct – it's what __getitem__ expects.
            yield self[column.name]

    def __getitem__(self, name):
        """
        Returns the final rendered value for a cell in the row, given the name
        of a column.

        """
        bound_column = self.table.columns[name]

        def value():
            try:
                raw = bound_column.accessor.resolve(self.record)
            except (TypeError, AttributeError, KeyError, ValueError) as e:
                raw = None
            return raw if raw is not None else bound_column.default

        kwargs = {
            'value':        value,  # already a function
            'record':       lambda: self.record,
            'column':       lambda: bound_column.column,
            'bound_column': lambda: bound_column,
            'bound_row':    lambda: self,
            'table':        lambda: self._table,
        }
        render_FOO = 'render_' + bound_column.name
        render = getattr(self.table, render_FOO, bound_column.column.render)

        # just give a list of all available methods
        funcs = ifilter(curry(hasattr, inspect), ('getfullargspec', 'getargspec'))
        spec = getattr(inspect, next(funcs))
        # only provide the arguments that the func is interested in
        kw = {}
        for name in spec(render).args:
            if name == 'self':
                continue
            kw[name] = kwargs[name]()
        return render(**kw)

    def __contains__(self, item):
        """Check by both row object and column name."""
        if isinstance(item, basestring):
            return item in self.table._columns
        else:
            return item in self


class BoundRows(object):
    """
    Container for spawning :class:`.BoundRow` objects.

    The :attr:`.Table.rows` attribute is a :class:`.BoundRows` object.
    It provides functionality that would not be possible with a simple iterator
    in the table class.

    :type table: :class:`.Table` object
    :param table: the table in which the rows exist.

    """
    def __init__(self, table):
        self.table = table

    def __iter__(self):
        """Convience method for :meth:`.BoundRows.all`"""
        for record in self.table.data:
            yield BoundRow(self.table, record)

    def __len__(self):
        """Returns the number of rows in the table."""
        return len(self.table.data)

    # for compatibility with QuerySetPaginator
    count = __len__

    def __getitem__(self, key):
        """Allows normal list slicing syntax to be used."""
        if isinstance(key, slice):
            return imap(lambda record: BoundRow(self.table, record),
                        self.table.data[key])
        elif isinstance(key, int):
            return BoundRow(self.table, self.table.data[key])
        else:
            raise TypeError('Key must be a slice or integer.')
