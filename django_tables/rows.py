class BoundRow(object):
    """Represents a single row of in a table.

    BoundRow provides a layer on top of the table data that exposes final
    rendered cell values for the table. This means that formatting (via
    Column.formatter or overridden Column.render in subclasses) applied to the
    values from the table's data.
    """
    def __init__(self, table, data):
        self.table = table
        self.data = data

    def __iter__(self):
        for value in self.values:
            yield value

    def __getitem__(self, name):
        """Returns the final rendered value for a cell in the row, given the
        name of a column.
        """
        bound_column = self.table.columns[name]
        # use custom render_FOO methods on the table
        custom = getattr(self.table, 'render_%s' % name, None)
        if custom:
            return custom(bound_column, self)
        return bound_column.column.render(self.table, bound_column, self)

    def __contains__(self, item):
        """Check by both row object and column name."""
        if isinstance(item, basestring):
            return item in self.table._columns
        else:
            return item in self

    @property
    def values(self):
        for column in self.table.columns:
            yield self[column.name]


class Rows(object):
    """Container for spawning BoundRows.

    This is bound to a table and provides it's ``rows`` property. It
    provides functionality that would not be possible with a simple
    iterator in the table class.
    """
    def __init__(self, table):
        self.table = table

    def all(self):
        """Return all rows."""
        for row in self.table.data:
            yield BoundRow(self.table, row)

    def page(self):
        """Return rows on current page (if paginated)."""
        if not hasattr(self.table, 'page'):
            return None
        return iter(self.table.page.object_list)

    def __iter__(self):
        return iter(self.all())

    def __len__(self):
        return len(self.table.data)

    # for compatibility with QuerySetPaginator
    count = __len__

    def __getitem__(self, key):
        if isinstance(key, slice):
            result = list()
            for row in self.table.data[key]:
                result.append(BoundRow(self.table, row))
            return result
        elif isinstance(key, int):
            return BoundRow(self.table, self.table.data[key])
        else:
            raise TypeError('Key must be a slice or integer.')
