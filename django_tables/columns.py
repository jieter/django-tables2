# -*- coding: utf-8 -*-
from django.utils.encoding import force_unicode, StrAndUnicode
from django.utils.datastructures import SortedDict
from django.utils.text import capfirst


class Column(object):
    """Represents a single column of a table.

    ``verbose_name`` defines a display name for this column used for output.

    You can use ``visible`` to flag the column as hidden by default.
    However, this can be overridden by the ``visibility`` argument to the
    table constructor. If you want to make the column completely unavailable
    to the user, set ``inaccessible`` to True.

    Setting ``sortable`` to False will result in this column being unusable
    in ordering. You can further change the *default* sort direction to
    descending using ``direction``. Note that this option changes the actual
    direction only indirectly. Normal und reverse order, the terms
    django-tables exposes, now simply mean different things.

    Data can be formatted by using ``formatter``, which accepts a callable as
    an argument (e.g. lambda x: x.upper())
    """
    # Tracks each time a Column instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, verbose_name=None, accessor=None, default=None,
                 visible=True, sortable=None, formatter=None):
        if not (accessor is None or isinstance(accessor, basestring) or
                callable(accessor)):
            raise TypeError('accessor must be a string or callable, not %s' %
                            accessor.__class__.__name__)
        if callable(accessor) and default is not None:
            raise TypeError('accessor must be string when default is used, not'
                            ' callable')
        self.accessor = accessor
        self._default = default
        self.formatter = formatter
        self.sortable = sortable
        self.verbose_name = verbose_name
        self.visible = visible

        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

    @property
    def default(self):
        """Since ``Column.default`` property may be a callable, this function
        handles access.
        """
        return self._default() if callable(self._default) else self._default

    def render(self, table, bound_column, bound_row):
        """Returns a cell's content.
        This method can be overridden by ``render_FOO`` methods on the table or
        by subclassing ``Column``.
        """
        return table.data.data_for_cell(bound_column=bound_column,
                                        bound_row=bound_row)


class CheckBoxColumn(Column):
    """A subclass of Column that renders its column data as a checkbox

    ``name`` is the html name of the checkbox.
    """
    def __init__(self, attrs=None, *args, **kwargs):
        super(CheckBoxColumn, self).__init__(*args, **kwargs)
        self.attrs = attrs or {}

    def render(self, bound_column, bound_row):
        from django.template import Template, Context
        attrs = {'name': bound_column.name}
        attrs.update(self.attrs)
        t = Template('<input type="checkbox" value="{{ value }}" '
                     '{% for attr, value in attrs.iteritems %}'
                     '{{ attr|escapejs }}="{{ value|escapejs }}" '
                     '{% endfor %}/>')
        return t.render(Context({
            'value': self.value(bound_column=bound_column,
                                bound_row=bound_row),
            'attrs': attrs,
        }))


class BoundColumn(StrAndUnicode):
    """'Runtime' version of ``Column`` that is bound to a table instance,
    and thus knows about the table's data. The difference between BoundColumn
    and Column, is a BoundColumn is aware of actual values (e.g. its name)
    where-as Column is not.

    For convenience, all Column properties are available from this class.
    """
    def __init__(self, table, column, name):
        """*table* - the table in which this column exists
        *column* - the column class
        *name* – the variable name used when the column was defined in the
                 table class
        """
        self.table = table
        self.column = column
        self.name = name

    def __unicode__(self):
        s = self.column.verbose_name or self.name.replace('_', ' ')
        return capfirst(force_unicode(s))

    @property
    def accessor(self):
        return self.column.accessor or self.name

    @property
    def default(self):
        return self.column.default

    @property
    def formatter(self):
        return self.column.formatter

    @property
    def sortable(self):
        if self.column.sortable is not None:
            return self.column.sortable
        elif self.table._meta.sortable is not None:
            return self.table._meta.sortable
        else:
            return True  # the default value

    @property
    def verbose_name(self):
        return self.column.verbose_name

    @property
    def visible(self):
        return self.column.visible


class Columns(object):
    """Container for spawning BoundColumns.

    This is bound to a table and provides its ``columns`` property. It
    provides access to those columns in different ways (iterator,
    item-based, filtered and unfiltered etc), stuff that would not be
    possible with a simple iterator in the table class.
    """
    def __init__(self, table):
        self.table = table
        # ``self._columns`` attribute stores the bound columns (columns that
        # have a real name, )
        self._columns = SortedDict()

    def _spawn_columns(self):
        # (re)build the "_columns" cache of BoundColumn objects (note that
        # ``base_columns`` might have changed since last time); creating
        # BoundColumn instances can be costly, so we reuse existing ones.
        new_columns = SortedDict()
        for name, column in self.table.base_columns.items():
            if name in self._columns:
                new_columns[name] = self._columns[name]
            else:
                new_columns[name] = BoundColumn(self.table, column, name)
        self._columns = new_columns

    def all(self):
        """Iterate through all columns, regardless of visiblity (as
        opposed to ``__iter__``.

        This is used internally a lot.
        """
        self._spawn_columns()
        for column in self._columns.values():
            yield column

    def items(self):
        self._spawn_columns()
        for r in self._columns.items():
            yield r

    def names(self):
        self._spawn_columns()
        for r in self._columns.keys():
            yield r

    def index(self, name):
        self._spawn_columns()
        return self._columns.keyOrder.index(name)

    def sortable(self):
        """Iterate through all sortable columns.

        This is primarily useful in templates, where iterating over the full
        set and checking {% if column.sortable %} can be problematic in
        conjunction with e.g. {{ forloop.last }} (the last column might not
        be the actual last that is rendered).
        """
        for column in self.all():
            if column.sortable:
                yield column

    def __iter__(self):
        """Iterate through all *visible* bound columns.

        This is primarily geared towards table rendering.
        """
        for column in self.all():
            if column.visible:
                yield column

    def __contains__(self, item):
        """Check by both column object and column name."""
        self._spawn_columns()
        if isinstance(item, basestring):
            return item in self.names()
        else:
            return item in self.all()

    def __len__(self):
        self._spawn_columns()
        return len([1 for c in self._columns.values() if c.visible])

    def __getitem__(self, index):
        """Return a column by name or index."""
        self._spawn_columns()
        if isinstance(index, int):
            return self._columns.value_for_index(index)
        elif isinstance(index, basestring):
            return self._columns[index]
        else:
            raise TypeError('row indices must be integers or str, not %s' %
                            index.__class__.__name__)
