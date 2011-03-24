# -*- coding: utf-8 -*-

class BoundRow(object):
    """Represents a *specific* row in a table.

    :class:`BoundRow` objects expose rendered versions of raw table data. This
    means that formatting (via :attr:`Column.formatter` or an overridden
    :meth:`Column.render` method) is applied to the values from the table's
    data.

    To access the rendered value of each cell in a row, just iterate over it:

    .. code-block:: python

        >>> import django_tables as tables
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

    """
    def __init__(self, table, record):
        """Initialise a new :class:`BoundRow` object where:

        * *table* is the :class:`Table` in which this row exists.
        * *record* is a single record from the data source that is posed to
          populate the row. A record could be a :class:`Model` object, a
          ``dict``, or something else.

        """
        self._table = table
        self._record = record

    @property
    def table(self):
        """The associated :term:`table`."""
        return self._table

    @property
    def record(self):
        """The data record from the data source which is used to populate this
        row with data.

        """
        return self._record

    def __iter__(self):
        """Iterate over the rendered values for cells in the row.

        Under the hood this method just makes a call to :meth:`__getitem__` for
        each cell.

        """
        for column in self.table.columns:
            # this uses __getitem__, using the name (rather than the accessor)
            # is correct – it's what __getitem__ expects.
            yield self[column.name]

    def __getitem__(self, name):
        """Returns the final rendered value for a cell in the row, given the
        name of a column.
        """
        bound_column = self.table.columns[name]
        # use custom render_FOO methods on the table
        custom = getattr(self.table, 'render_%s' % name, None)
        if custom:
            return custom(bound_column, self)
        return bound_column.column.render(table=self.table,
                                          bound_column=bound_column,
                                          bound_row=self)

    def __contains__(self, item):
        """Check by both row object and column name."""
        if isinstance(item, basestring):
            return item in self.table._columns
        else:
            return item in self


class Rows(object):
    """Container for spawning BoundRows.

    This is bound to a table and provides it's ``rows`` property. It
    provides functionality that would not be possible with a simple
    iterator in the table class.
    """
    def __init__(self, table):
        """Initialise a :class:`Rows` object. *table* is the :class:`Table`
        object in which the rows exist.

        """
        self.table = table

    def all(self):
        """Return an iterable for all :class:`BoundRow` objects in the table.

        """
        for row in self.table.data:
            yield BoundRow(self.table, row)

    def page(self):
        """If the table is paginated, return an iterable of :class:`BoundRow`
        objects that appear on the current page, otherwise return None.

        """
        if not hasattr(self.table, 'page'):
            return None
        return iter(self.table.page.object_list)

    def __iter__(self):
        """Convience method for all()"""
        return self.all()

    def __len__(self):
        """Returns the number of rows in the table."""
        return len(self.table.data)

    # for compatibility with QuerySetPaginator
    count = __len__

    def __getitem__(self, key):
        """Allows normal list slicing syntax to be used."""
        if isinstance(key, slice):
            result = list()
            for row in self.table.data[key]:
                result.append(BoundRow(self.table, row))
            return result
        elif isinstance(key, int):
            return BoundRow(self.table, self.table.data[key])
        else:
            raise TypeError('Key must be a slice or integer.')
