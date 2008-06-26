import copy
from django.utils.datastructures import SortedDict
from django.utils.encoding import StrAndUnicode
from django.utils.text import capfirst
from columns import Column

__all__ = ('BaseTable', 'Table', 'options')

def sort_table(data, order_by):
    """Sort a list of dicts according to the fieldnames in the
    ``order_by`` iterable. Prefix with hypen for reverse.

    Dict values can be callables.
    """
    def _cmp(x, y):
        for name, reverse in instructions:
            lhs, rhs = x.get(name), y.get(name)
            res = cmp((callable(lhs) and [lhs(x)] or [lhs])[0],
                      (callable(rhs) and [rhs(y)] or [rhs])[0])
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

# A common use case is passing incoming query values directly into the
# table constructor - data that can easily be invalid, say if manually
# modified by a user. So by default, such errors will be silently
# ignored. Set the option below to False if you want an exceptions to be
# raised instead.
class DefaultOptions(object):
    IGNORE_INVALID_OPTIONS = True
options = DefaultOptions()

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
        self._rows = Rows(self)
        self._columns = Columns(self)

        self.order_by = order_by

        # Make a copy so that modifying this will not touch the class
        # definition. Note that this is different from forms, where the
        # copy is made available in a ``fields`` attribute. See the
        # ``Table`` class docstring for more information.
        self.base_columns = copy.deepcopy(type(self).base_columns)

    def _build_snapshot(self):
        """Rebuilds the table whenever it's options change.

        Whenver the table options change, e.g. say a new sort order,
        this method will be asked to regenerate the actual table from
        the linked data source.

        In the case of this base table implementation, a copy of the
        source data is created, and then modified appropriately.

        # TODO: currently this is called whenever data changes; it is
        # probably much better to do this on-demand instead, when the
        # data is *needed* for the first time.
        """

        # reset caches
        self._columns._reset()
        self._rows._reset()

        snapshot = copy.copy(self._data)
        for row in snapshot:
            # add data that is missing from the source. we do this now so
            # that the colunn ``default`` and ``data`` values can affect
            # sorting (even when callables are used)!
            # This is a design decision - the alternative would be to
            # resolve the values when they are accessed, and either do not
            # support sorting them at all, or run the callables during
            # sorting.
            for column in self.columns.all():
                name_in_source = column.declared_name
                if column.column.data:
                    if callable(column.column.data):
                        # if data is a callable, use it's return value
                        row[name_in_source] = column.column.data(BoundRow(self, row))
                    else:
                        name_in_source = column.column.data

                # the following will be True if:
                #  * the source does not provide that column or provides None
                #  * the column did provide a data callable that returned None
                if row.get(name_in_source, None) is None:
                    row[name_in_source] = column.get_default(BoundRow(self, row))

        if self.order_by:
            sort_table(snapshot, self._cols_to_fields(self.order_by))
        self._snapshot = snapshot

    def _get_data(self):
        if self._snapshot is None:
            self._build_snapshot()
        return self._snapshot
    data = property(lambda s: s._get_data())

    def _cols_to_fields(self, names):
        """Utility function. Given a list of column names (as exposed to
        the user), converts column names to the names we have to use to
        retrieve a column's data from the source.

        Usually, the name used in the table declaration is used for accessing
        the source (while a column can define an alias-like name that will
        be used to refer to it from the "outside"). However, a column can
        override this by giving a specific source field name via ``data``.

        Supports prefixed column names as used e.g. in order_by ("-field").
        """
        result = []
        for ident in names:
            # handle order prefix
            if ident[:1] == '-':
                name = ident[1:]
                prefix = '-'
            else:
                name = ident
                prefix = ''
            # find the field name
            column = self.columns[name]
            if column.column.data and not callable(column.column.data):
                name_in_source = column.column.data
            else:
                name_in_source = column.declared_name
            result.append(prefix + name_in_source)
        return result

    def _validate_column_name(self, name, purpose):
        """Return True/False, depending on whether the column ``name`` is
        valid for ``purpose``. Used to validate things like ``order_by``
        instructions.

        Can be overridden by subclasses to impose further restrictions.
        """
        if purpose == 'order_by':
            return name in self.columns and\
                   self.columns[name].column.sortable
        else:
            return True

    def _set_order_by(self, value):
        if self._snapshot is not None:
            self._snapshot = None
        # accept both string and tuple instructions
        order_by = (isinstance(value, basestring) \
            and [value.split(',')] \
            or [value])[0]
        if order_by:
            # validate, remove all invalid order instructions
            validated_order_by = []
            for o in order_by:
                if self._validate_column_name((o[:1]=='-' and [o[1:]] or [o])[0], "order_by"):
                    validated_order_by.append(o)
                elif not options.IGNORE_INVALID_OPTIONS:
                    raise ValueError('Column name %s is invalid.' % o)
            self._order_by = OrderByTuple(validated_order_by)
        else:
            self._order_by = ()
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

    # just to make those readonly
    columns = property(lambda s: s._columns)
    rows = property(lambda s: s._rows)

    def as_html(self):
        pass

    def update(self):
        """Update the table based on it's current options.

        Normally, you won't have to call this method, since the table
        updates itself (it's caches) automatically whenever you change
        any of the properties. However, in some rare cases those
        changes might not be picked up, for example if you manually
        change ``base_columns`` or any of the columns in it.
        """
        self._build_snapshot()

    def paginate(self, klass, *args, **kwargs):
        page = kwargs.pop('page', 1)
        self.paginator = klass(self.rows, *args, **kwargs)
        self.page = self.paginator.page(page)


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
    possible with a simple iterator in the table class.

    Note that when you define your column using a name override, e.g.
    ``author_name = tables.Column(name="author")``, then the column will
    be exposed by this container as "author", not "author_name".
    """
    def __init__(self, table):
        self.table = table
        self._columns = SortedDict()

    def _reset(self):
        """Used by parent table class."""
        self._columns = SortedDict()

    def _spawn_columns(self):
        # (re)build the "_columns" cache of BoundColumn objects (note that
        # ``base_columns`` might have changed since last time); creating
        # BoundColumn instances can be costly, so we reuse existing ones.
        new_columns = SortedDict()
        for decl_name, column in self.table.base_columns.items():
            # take into account name overrides
            exposed_name = column.name or decl_name
            if exposed_name in self._columns:
                new_columns[exposed_name] = self._columns[exposed_name]
            else:
                new_columns[exposed_name] = BoundColumn(self, column, decl_name)
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

    def __iter__(self):
        """Iterate through all *visible* bound columns.

        This is primarily geared towards table rendering.
        """
        for column in self.all():
            if column.column.visible:
                yield column

    def __contains__(self, item):
        """Check by both column object and column name."""
        self._spawn_columns()
        if isinstance(item, basestring):
            return item in self.names()
        else:
            return item in self.all()

    def __getitem__(self, name):
        """Return a column by name."""
        self._spawn_columns()
        return self._columns[name]


class BoundColumn(StrAndUnicode):
    """'Runtime' version of ``Column`` that is bound to a table instance,
    and thus knows about the table's data.

    Note that the name that is passed in tells us how this field is
    delared in the bound table. The column itself can overwrite this name.
    While the overwritten name will be hat mostly counts, we need to
    remember the one used for declaration as well, or we won't know how
    to read a column's value from the source.
    """
    def __init__(self, table, column, name):
        self.table = table
        self.column = column
        self.declared_name = name
        # expose some attributes of the column more directly
        self.sortable = column.sortable
        self.visible = column.visible

    name = property(lambda s: s.column.name or s.declared_name)

    def get_default(self, row):
        """Since a column's ``default`` property may be a callable, we need
        this function to resolve it when needed.

        Make sure ``row`` is a ``BoundRow`` objects, since that is what
        we promise the callable will get.
        """
        if callable(self.column.default):
            return self.column.default(row)
        return self.column.default

    def _get_values(self):
        # TODO: build a list of values used
        pass
    values = property(_get_values)

    def __unicode__(self):
        return capfirst(self.column.verbose_name or self.name.replace('_', ' '))

    def as_html(self):
        pass

class Rows(object):
    """Container for spawning BoundRows.

    This is bound to a table and provides it's ``rows`` property. It
    provides functionality that would not be possible with a simple
    iterator in the table class.
    """
    def __init__(self, table, row_klass=None):
        self.table = table
        self.row_klass = row_klass and row_klass or BoundRow

    def _reset(self):
        pass   # we currently don't use a cache

    def all(self):
        """Return all rows."""
        for row in self.table.data:
            yield self.row_klass(self.table, row)

    def page(self):
        """Return rows on current page (if paginated)."""
        if not hasattr(self.table, 'page'):
            return None
        return iter(self.table.page.object_list)

    def __iter__(self):
        return iter(self.all())

    def __len__(self):
        return len(self.table.data)

    def __getitem__(self, key):
        if isinstance(key, slice):
            result = list()
            for row in self.table.data[key]:
                result.append(self.row_klass(self.table, row))
            return result
        elif isinstance(key, int):
            return self.row_klass(self.table, self.table.data[key])
        else:
            raise TypeError('Key must be a slice or integer.')

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
        """Returns this row's value for a column. All other access methods,
        e.g. __iter__, lead ultimately to this."""

        # We are supposed to return ``name``, but the column might be
        # named differently in the source data.
        result =  self.data[self.table._cols_to_fields([name])[0]]

        # if the field we are pointing to is a callable, remove it
        if callable(result):
            result = result(self)
        return result

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