# coding: utf-8
from django.db import models
from django.db.models.fields import FieldDoesNotExist
from .utils import A, getargspec


class BoundRow(object):
    """
    Represents a *specific* row in a table.

    `.BoundRow` objects are a container that make it easy to access the
    final 'rendered' values for cells in a row. You can simply iterate over a
    `.BoundRow` object and it will take care to return values rendered
    using the correct method (e.g. :ref:`table.render_FOO`)

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

    :param  table: is the `.Table` in which this row exists.
    :param record: a single record from the :term:`table data` that is used to
                   populate the row. A record could be a `~django.db.Model`
                   object, a `dict`, or something else.

    """
    def __init__(self, record, table):
        self._record = record
        self._table = table

    @property
    def table(self):
        """The associated `.Table` object."""
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
        `.BoundRow.__getitem__` for each cell.
        """
        for column, value in self.items():
            # this uses __getitem__, using the name (rather than the accessor)
            # is correct – it's what __getitem__ expects.
            yield value

    def __getitem__(self, name):
        """
        Returns the final rendered value for a cell in the row, given the name
        of a column.
        """
        bound_column = self.table.columns[name]

        value = None
        # We need to take special care here to allow get_FOO_display()
        # methods on a model to be used if available. See issue #30.
        path, _, remainder = bound_column.accessor.rpartition('.')
        penultimate = A(path).resolve(self.record, quiet=True)
        # If the penultimate is a model and the remainder is a field
        # using choices, use get_FOO_display().
        if isinstance(penultimate, models.Model):
            try:
                field = penultimate._meta.get_field(remainder)
                display = getattr(penultimate, 'get_%s_display' % remainder, None)
                if field.choices and display:
                    value = display()
                    remainder = None
            except FieldDoesNotExist:
                pass
        # Fall back to just using the original accessor (we just need
        # to follow the remainder).
        if remainder:
            value = A(remainder).resolve(penultimate, quiet=True)

        if value in bound_column.column.empty_values:
            return bound_column.default

        available = {
            'value':        value,
            'record':       self.record,
            'column':       bound_column.column,
            'bound_column': bound_column,
            'bound_row':    self,
            'table':        self._table,
        }
        expected = {}

        # provide only the arguments expected by `render`
        argspec = getargspec(bound_column.render)
        if argspec.keywords:
            expected = available
        else:
            for key, value in available.items():
                if key in argspec.args[1:]:
                    expected[key] = value

        return bound_column.render(**expected)

    def __contains__(self, item):
        """Check by both row object and column name."""
        if isinstance(item, basestring):
            return item in self.table._columns
        else:
            return item in self

    def items(self):
        """
        Returns iterator yielding ``(bound_column, cell)`` pairs.

        *cell* is ``row[name]`` -- the rendered unicode value that should be
        ``rendered within ``<td>``.
        """
        for column in self.table.columns:
            yield (column, self[column.name])


class BoundRows(object):
    """
    Container for spawning `.BoundRow` objects.

    :param  data: iterable of records
    :param table: the table in which the rows exist

    This is used for `.Table.rows`.
    """
    def __init__(self, data, table):
        self.data = data
        self.table = table

    def __iter__(self):
        for record in self.data:
            yield BoundRow(record, table=self.table)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        """
        Slicing returns a new `.BoundRows` instance, indexing returns a single
        `.BoundRow` instance.
        """
        container = BoundRows if isinstance(key, slice) else BoundRow
        return container(self.data[key], table=self.table)
