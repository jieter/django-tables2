import copy
from django.utils.datastructures import SortedDict
from django.utils.encoding import StrAndUnicode
from columns import Column

__all__ = ('BaseTable', 'Table')

def sort_table(data, order_by):
    """Sort a list of dicts according to the fieldnames in the
    ``order_by`` iterable. Prefix with hypen for reverse.
    """
    def _cmp(x, y):
        for name, reverse in instructions:
            res = cmp(x.get(name), y.get(name))
            if res != 0:
                return reverse and -res or res
        return 0
    instructions = []
    for o in order_by:
        if o.startswith('-'):
            instructions.append((o[1:], True,))
        else:
            instructions.append((o, False,))
    data.sort(cmp=_cmp)

class DeclarativeColumnsMetaclass(type):
    """
    Metaclass that converts Column attributes to a dictionary called
    'base_columns', taking into account parent class 'base_columns'
    as well.
    """
    def __new__(cls, name, bases, attrs, parent_cols_from=None):
        """
        The ``parent_cols_from`` argument determins from which attribute
        we read the columns of a base class that this table might be
        subclassing. This is useful for ``ModelTable`` (and possibly other
        derivatives) which might want to differ between the declared columns
        and others.

        Note that if the attribute specified in ``parent_cols_from`` is not
        found, we fall back to the default (``base_columns``), instead of
        skipping over that base. This makes a table like the following work:

            class MyNewTable(tables.ModelTable, MyNonModelTable):
                pass

        ``MyNewTable`` will be built by the ModelTable metaclass, which will
        call this base with a modified ``parent_cols_from`` argument
        specific to ModelTables. Since ``MyNonModelTable`` is not a
        ModelTable, and thus does not provide that attribute, the columns
        from that base class would otherwise be ignored.
        """

        # extract declared columns
        columns = [(column_name, attrs.pop(column_name))
           for column_name, obj in attrs.items()
           if isinstance(obj, Column)]
        columns.sort(lambda x, y: cmp(x[1].creation_counter,
                                      y[1].creation_counter))

        # If this class is subclassing other tables, add their fields as
        # well. Note that we loop over the bases in *reverse* - this is
        # necessary to preserve the correct order of columns.
        for base in bases[::-1]:
            col_attr = (parent_cols_from and hasattr(base, parent_cols_from)) \
                and parent_cols_from\
                or 'base_columns'
            if hasattr(base, col_attr):
                columns = getattr(base, col_attr).items() + columns
        # Note that we are reusing an existing ``base_columns`` attribute.
        # This is because in certain inheritance cases (mixing normal and
        # ModelTables) this metaclass might be executed twice, and we need
        # to avoid overriding previous data (because we pop() from attrs,
        # the second time around columns might not be registered again).
        # An example would be:
        #    class MyNewTable(MyOldNonModelTable, tables.ModelTable): pass
        if not 'base_columns' in attrs:
            attrs['base_columns'] = SortedDict()
        attrs['base_columns'].update(SortedDict(columns))

        return type.__new__(cls, name, bases, attrs)

class OrderByTuple(tuple, StrAndUnicode):
        """Stores 'order by' instructions; Currently only used to render
        to the output (especially in templates) in a format we understand
        as input.
        """
        def __unicode__(self):
            return ",".join(self)

class BaseTable(object):
    def __init__(self, data, order_by=None):
        """Create a new table instance with the iterable ``data``.

        If ``order_by`` is specified, the data will be sorted accordingly.

        Note that unlike a ``Form``, tables are always bound to data. Also
        unlike a form, the ``columns`` attribute is read-only and returns
        ``BoundColum`` wrappers, similar to the ``BoundField``'s you get
        when iterating over a form. This is because the table iterator
        already yields rows, and we need an attribute via which to expose
        the (visible) set of (bound) columns - ``Table.columns`` is simply
        the perfect fit for this. Instead, ``base_colums`` is copied to
        table instances, so modifying that will not touch the class-wide
        column list.
        """
        self._data = data
        self._snapshot = None      # will store output dataset (ordered...)
        self._rows = None          # will store BoundRow objects
        self._columns = Columns(self)
        self._order_by = order_by

        # Make a copy so that modifying this will not touch the class
        # definition. Note that this is different from forms, where the
        # copy is made available in a ``fields`` attribute. See the
        # ``Table`` class docstring for more information.
        self.base_columns = copy.deepcopy(type(self).base_columns)

    def _build_snapshot(self):
        snapshot = copy.copy(self._data)
        for row in snapshot:
            # delete unknown columns and add missing ones; note that
            # self.columns already accounts for column name overrides.
            for column in row.keys():
                if not column in self.columns:
                    del row[column]
            for colname, colobj in self.columns.items():
                if not colname in row:
                    row[colname] = colobj.column.default
        if self.order_by:
            sort_table(snapshot, self.order_by)
        self._snapshot = snapshot

    def _get_data(self):
        if self._snapshot is None:
            self._build_snapshot()
        return self._snapshot
    data = property(lambda s: s._get_data())

    def _set_order_by(self, value):
        if self._snapshot is not None:
            self._snapshot = None
        # accept both string and tuple instructions
        self._order_by = (isinstance(value, basestring) \
            and [value.split(',')] \
            or [value])[0]
        # validate, remove all invalid order instructions
        def can_be_used(o):
           c = (o[:1]=='-' and [o[1:]] or [o])[0]
           return c in self.base_columns and self.base_columns[c].sortable
        self._order_by = OrderByTuple([o for o in self._order_by if can_be_used(o)])
        # TODO: optionally, throw an exception
    order_by = property(lambda s: s._order_by, _set_order_by)

    def __unicode__(self):
        return self.as_html()

    def __iter__(self):
        for row in self.rows:
            yield row

    def __getitem__(self, name):
        try:
            column = self.columns[name]
        except KeyError:
            raise KeyError('Key %r not found in Table' % name)
        return BoundColumn(self, column, name)

    columns = property(lambda s: s._columns)  # just to make it readonly

    def _get_rows(self):
        for row in self.data:
            yield BoundRow(self, row)
    rows = property(_get_rows)

    def as_html(self):
        pass

class Table(BaseTable):
    "A collection of columns, plus their associated data rows."
    # This is a separate class from BaseTable in order to abstract the way
    # self.columns is specified.
    __metaclass__ = DeclarativeColumnsMetaclass


class Columns(object):
    """Container for spawning BoundColumns.

    This is bound to a table and provides it's ``columns`` property. It
    provides access to those columns in different ways (iterator,
    item-based, filtered and unfiltered etc)., stuff that would not be
    possible with a simple iterator on the table class.

    Note that when you define your column using a name override, e.g.
    ``author_name = tables.Column(name="author")``, then the column will
    be exposed by this container as "author", not "author_name".
    """
    def __init__(self, table):
        self.table = table
        self._columns = SortedDict()

    def _spawn_columns(self):
        # (re)build the "_columns" cache of BoundColumn objects (note that
        # ``base_columns`` might have changed since last time); creating
        # BoundColumn instances can be costly, so we reuse existing ones.
        new_columns = SortedDict()
        for name, column in self.table.base_columns.items():
            name = column.name or name  # take into account name overrides
            if name in self._columns:
                new_columns[name] = self._columns[name]
            else:
                new_columns[name] = BoundColumn(self, column, name)
        self._columns = new_columns

    def all(self):
        self._spawn_columns()
        for column in self._columns.values():
            yield column

    def items(self):
        self._spawn_columns()
        for r in self._columns.items():
            yield r

    def keys(self):
        self._spawn_columns()
        for r in self._columns.keys():
            yield r

    def index(self, name):
        self._spawn_columns()
        return self._columns.keyOrder.index(name)

    def __iter__(self):
        for column in self.all():
            if column.column.visible:
                yield column

    def __contains__(self, item):
        """Check by both column object and column name."""
        self._spawn_columns()
        if isinstance(item, basestring):
            return item in self.keys()
        else:
            return item in self.all()

    def __getitem__(self, name):
        """Return a column by name."""
        self._spawn_columns()
        return self._columns[name]


class BoundColumn(StrAndUnicode):
    """'Runtime' version of ``Column`` that is bound to a table instance,
    and thus knows about the table's data.
    """
    def __init__(self, table, column, name):
        self.table = table
        self.column = column
        self.name = column.name or name
        # expose some attributes of the column more directly
        self.sortable = column.sortable
        self.visible = column.visible

    def _get_values(self):
        # TODO: build a list of values used
        pass
    values = property(_get_values)

    def __unicode__(self):
        return self.column.verbose_name or self.name

    def as_html(self):
        pass

class BoundRow(object):
    """Represents a single row of data, bound to a table.

    Tables will spawn these row objects, wrapping around the actual data
    stored in a row.
    """
    def __init__(self, table, data):
        self.table = table
        self.data = data

    def __iter__(self):
        for value in self.values:
            yield value

    def __getitem__(self, name):
        "Returns the value for the column with the given name."
        return self.data[name]

    def __contains__(self, item):
        """Check by both row object and column name."""
        if isinstance(item, basestring):
            return item in self.table._columns
        else:
            return item in self

    def _get_values(self):
        for column in self.table.columns:
            yield self[column.name]
    values = property(_get_values)

    def as_html(self):
        pass