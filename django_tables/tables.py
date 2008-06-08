import copy
from django.utils.datastructures import SortedDict
from django.utils.encoding import StrAndUnicode
from columns import Column

__all__ = ('BaseTable', 'Table', 'Row')

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

class Row(object):
    def __init__(self, data):
        self.data = data
    def as_html(self):
        pass

from smartinspect.auto import *
si.enabled = True

class DeclarativeColumnsMetaclass(type):
    """
    Metaclass that converts Column attributes to a dictionary called
    'base_columns', taking into account parent class 'base_columns'
    as well.
    """
    @si_main.track
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

class BaseTable(object):
    def __init__(self, data, order_by=None):
        """Create a new table instance with the iterable ``data``.

        If ``order_by`` is specified, the data will be sorted accordingly.

        Note that unlike a ``Form``, tables are always bound to data.
        """
        self._data = data
        self._data_cache = None  # will store output dataset (ordered...)
        self._row_cache = None   # will store Row objects
        self._order_by = order_by

        # The base_columns class attribute is the *class-wide* definition
        # of columns. Because a particular *instance* of the class might
        # want to alter self.columns, we create self.columns here by copying
        # ``base_columns``. Instances should always modify self.columns;
        # they should not modify self.base_columns.
        self.columns = copy.deepcopy(self.base_columns)

    def _build_data_cache(self):
        snapshot = copy.copy(self._data)
        for row in snapshot:
            # delete unknown column, and add missing ones
            for column in row.keys():
                if not column in self.columns:
                    del row[column]
            for column in self.columns.keys():
                if not column in row:
                    row[column] = self.columns[column].default
        if self.order_by:
            sort_table(snapshot, self.order_by)
        self._data_cache = snapshot

    def _get_data(self):
        if self._data_cache is None:
            self._build_data_cache()
        return self._data_cache
    data = property(lambda s: s._get_data())

    def _set_order_by(self, value):
        if self._data_cache is not None:
            self._data_cache = None
        self._order_by = isinstance(value, (tuple, list)) and value or (value,)
        # validate, remove all invalid order instructions
        def can_be_used(o):
           c = (o[:1]=='-' and [o[1:]] or [o])[0]
           return c in self.columns and self.columns[c].sortable
        self._order_by = [o for o in self._order_by if can_be_used(o)]
        # TODO: optionally, throw an exception
    order_by = property(lambda s: s._order_by, _set_order_by)

    def __unicode__(self):
        return self.as_html()

    def __iter__(self):
        for name, column in self.columns.items():
            yield BoundColumn(self, column, name)

    def __getitem__(self, name):
        try:
            column = self.columns[name]
        except KeyError:
            raise KeyError('Key %r not found in Table' % name)
        return BoundColumn(self, column, name)

    def as_html(self):
        pass

class Table(BaseTable):
    "A collection of columns, plus their associated data rows."
    # This is a separate class from BaseTable in order to abstract the way
    # self.columns is specified.
    __metaclass__ = DeclarativeColumnsMetaclass

class BoundColumn(StrAndUnicode):
    """'Runtime' version of ``Column`` that is bound to a table instance,
    and thus knows about the table's data.
    """
    def _get_values(self):
        # build a list of values used
        pass
    values = property(_get_values)

    def __unicode__(self):
        """Renders this field as an HTML widget."""
        return self.as_html()

    def as_html(self):
        pass