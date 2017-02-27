# coding: utf-8


from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.utils import six

from .columns.linkcolumn import BaseLinkColumn
from .utils import A, AttributeDict, call_with_appropriate, computed_values


class BoundRow(object):
    '''
    Represents a *specific* row in a table.

    `.BoundRow` objects are a container that make it easy to access the
    final 'rendered' values for cells in a row. You can simply iterate over a
    `.BoundRow` object and it will take care to return values rendered
    using the correct method (e.g. :ref:`table.render_FOO`)

    To access the rendered value of each cell in a row, just iterate over it::

        >>> import django_tables2 as tables
        >>> class SimpleTable(tables.Table):
        ...     a = tables.Column()
        ...     b = tables.CheckBoxColumn(attrs={'name': 'my_chkbox'})
        ...
        >>> table = SimpleTable([{'a': 1, 'b': 2}])
        >>> row = table.rows[0]  # we only have one row, so let's use it
        >>> for cell in row:
        ...     print(cell)
        ...
        1
        <input type="checkbox" name="my_chkbox" value="2" />

    Alternatively you can use row.get_cell() to retrieve a specific cell::

        >>> row.get_cell(0)
        1
        >>> row.get_cell(1)
        u'<input type="checkbox" name="my_chkbox" value="2" />'
        >>> row.get_cell(2)
        ...
        IndexError: list index out of range

    Finally you can also use the column names to retrieve a specific cell::

        >>> row.get_cell('a')
        1
        >>> row.get_cell('b')
        u'<input type="checkbox" name="my_chkbox" value="2" />'
        >>> row.get_cell('c')
        ...
        KeyError: 'c'

    Arguments:
        table: The `.Table` in which this row exists.
        record: a single record from the :term:`table data` that is used to
            populate the row. A record could be a `~django.db.Model` object, a
            `dict`, or something else.

    '''
    def __init__(self, record, table):
        self._record = record
        self._table = table

    @property
    def table(self):
        '''
        The associated `.Table` object.
        '''
        return self._table

    @property
    def attrs(self):
        '''
        Return the attributes for a certain row.
        '''
        cssClass = 'even' if next(self._table._counter) % 2 == 0 else 'odd'

        row_attrs = computed_values(self._table.row_attrs, self._record)

        if 'class' in row_attrs and row_attrs['class']:
            row_attrs['class'] += ' ' + cssClass
        else:
            row_attrs['class'] = cssClass

        return AttributeDict(row_attrs)

    @property
    def record(self):
        '''
        The data record from the data source which is used to populate this row
        with data.
        '''
        return self._record

    def __iter__(self):
        '''
        Iterate over the rendered values for cells in the row.

        Under the hood this method just makes a call to
        `.BoundRow.__getitem__` for each cell.
        '''
        for column, value in self.items():
            # this uses __getitem__, using the name (rather than the accessor)
            # is correct – it's what __getitem__ expects.
            yield value

    def _get_and_render_with(self, name, render_func, default):
        bound_column = self.table.columns[name]

        value = None
        accessor = A(bound_column.accessor)

        # We need to take special care here to allow get_FOO_display()
        # methods on a model to be used if available. See issue #30.
        penultimate, remainder = accessor.penultimate(self.record)

        # If the penultimate is a model and the remainder is a field
        # using choices, use get_FOO_display().
        if isinstance(penultimate, models.Model):
            try:
                field = accessor.get_field(self.record)
                display_fn = getattr(penultimate, 'get_%s_display' % remainder,
                                     None)
                if getattr(field, 'choices', ()) and display_fn:
                    value = display_fn()
                    remainder = None
            except FieldDoesNotExist:
                pass

        # Fall back to just using the original accessor
        if remainder:
            try:
                value = accessor.resolve(self.record)
            except Exception:
                # we need to account for non-field based columns (issue #257)
                is_linkcolumn = isinstance(bound_column.column, BaseLinkColumn)
                if is_linkcolumn and bound_column.column.text is not None:
                    return render_func(bound_column)

        if value in bound_column.column.empty_values:
            return default

        return render_func(bound_column, value)

    def get_cell(self, name):
        '''
        Returns the final rendered html for a cell in the row, given the name
        of a column.
        '''
        return self._get_and_render_with(
            name,
            render_func=self._call_render,
            default=self.table.columns[name].default
        )

    def _call_render(self, bound_column, value=None):
        '''
        Call the column's render method with appropriate kwargs
        '''

        return call_with_appropriate(bound_column.render, {
            'value': value,
            'record': self.record,
            'column': bound_column.column,
            'bound_column': bound_column,
            'bound_row': self,
            'table': self._table,
        })

    def get_cell_value(self, name):
        '''
        Returns the final rendered value (excluding any html) for a cell in the
        row, given the name of a column.
        '''
        return self._get_and_render_with(
            name,
            render_func=self._call_value,
            default=None
        )

    def _call_value(self, bound_column, value=None):
        '''Call the column's value method with appropriate kwargs'''

        return call_with_appropriate(bound_column.column.value, {
            'value': value,
            'record': self.record,
            'column': bound_column.column,
            'bound_column': bound_column,
            'bound_row': self,
            'table': self._table,
        })

    def __contains__(self, item):
        '''
        Check by both row object and column name.
        '''
        if isinstance(item, six.string_types):
            return item in self.table.columns
        else:
            return item in self

    def items(self):
        '''
        Returns iterator yielding ``(bound_column, cell)`` pairs.

        *cell* is ``row[name]`` -- the rendered unicode value that should be
        ``rendered within ``<td>``.
        '''
        for column in self.table.columns:
            yield (column, self.get_cell(column.name))


class BoundRows(object):
    '''
    Container for spawning `.BoundRow` objects.

    Arguments:
        data: iterable of records
        table: the `~.Table` in which the rows exist

    This is used for `~.Table.rows`.
    '''
    def __init__(self, data, table):
        self.data = data
        self.table = table

    def __iter__(self):
        for record in self.data:
            yield BoundRow(record, table=self.table)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        '''
        Slicing returns a new `~.BoundRows` instance, indexing returns a single
        `~.BoundRow` instance.
        '''
        container = BoundRows if isinstance(key, slice) else BoundRow
        return container(self.data[key], table=self.table)
