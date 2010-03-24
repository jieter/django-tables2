from django.core.exceptions import FieldError
from django.utils.datastructures import SortedDict
from base import BaseTable, DeclarativeColumnsMetaclass, \
    Column, BoundRow, Rows, TableOptions, rmprefix, toggleprefix


__all__ = ('ModelTable',)


class ModelTableOptions(TableOptions):
    def __init__(self, options=None):
        super(ModelTableOptions, self).__init__()
        self.model = getattr(options, 'model', None)
        self.columns = getattr(options, 'columns', None)
        self.exclude = getattr(options, 'exclude', None)


def columns_for_model(model, columns=None, exclude=None):
    """
    Returns a ``SortedDict`` containing form columns for the given model.

    ``columns`` is an optional list of field names. If provided, only the
    named model fields will be included in the returned column list.

    ``exclude`` is an optional list of field names. If provided, the named
    model fields will be excluded from the returned list of columns, even
    if they are listed in the ``fields`` argument.
    """

    field_list = []
    opts = model._meta
    for f in opts.fields + opts.many_to_many:
        if (columns and not f.name in columns) or \
           (exclude and f.name in exclude):
            continue
        column = Column() # TODO: chose correct column type, with right options
        if column:
            field_list.append((f.name, column))
    return SortedDict(field_list)


class BoundModelRow(BoundRow):
    """Special version of the BoundRow class that can handle model instances
    as data.

    We could simply have ModelTable spawn the normal BoundRow objects
    with the instance converted to a dict instead. However, this way allows
    us to support non-field attributes and methods on the model as well.
    """
    def __getitem__(self, name):
        """Overridden. Return this row's data for a certain column, with
        custom handling for model tables.
        """

        # find the column for the requested field, for reference
        boundcol = self.table._columns[name]

        # If the column has a name override (we know then that is was also
        # used for access, e.g. if the condition is true, then
        # ``boundcol.column.name == name``), we need to make sure we use the
        # declaration name to access the model field.
        if boundcol.column.data:
            if callable(boundcol.column.data):
                result = boundcol.column.data(self)
                if not result:
                    if boundcol.column.default is not None:
                        return boundcol.get_default(self)
                return result
            else:
                name = boundcol.column.data
        else:
            name = boundcol.declared_name


        # try to resolve relationships spanning attributes
        bits = name.split('__')
        current = self.data
        for bit in bits:
            # note the difference between the attribute being None and not
            # existing at all; assume "value doesn't exist" in the former
            # (e.g. a relationship has no value), raise error in the latter.
            # a more proper solution perhaps would look at the model meta
            # data instead to find out whether a relationship is valid; see
            # also ``_validate_column_name``, where such a mechanism is
            # already implemented).
            if not hasattr(current, bit):
                raise ValueError("Could not resolve %s from %s" % (bit, name))

            current = getattr(current, bit)
            if callable(current):
                current = current()
            # important that we break in None case, or a relationship
            # spanning across a null-key will raise an exception in the
            # next iteration, instead of defaulting.
            if current is None:
                break

        if current is None:
            # ...the whole name (i.e. the last bit) resulted in None
            if boundcol.column.default is not None:
                return boundcol.get_default(self)
        return current


class ModelRows(Rows):
    row_class = BoundModelRow

    def __init__(self, *args, **kwargs):
        super(ModelRows, self).__init__(*args, **kwargs)

    def _reset(self):
        self._length = None

    def __len__(self):
        """Use the queryset count() method to get the length, instead of
        loading all results into memory. This allows, for example,
        smart paginators that use len() to perform better.
        """
        if getattr(self, '_length', None) is None:
            self._length = self.table.data.count()
        return self._length

    # for compatibility with QuerySetPaginator
    count = __len__


class ModelTableMetaclass(DeclarativeColumnsMetaclass):
    def __new__(cls, name, bases, attrs):
        # Let the default form meta class get the declared columns; store
        # those in a separate attribute so that ModelTable inheritance with
        # differing models works as expected (the behaviour known from
        # ModelForms).
        self = super(ModelTableMetaclass, cls).__new__(
            cls, name, bases, attrs, parent_cols_from='declared_columns')
        self.declared_columns = self.base_columns

        opts = self._meta = ModelTableOptions(getattr(self, 'Meta', None))
        # if a model is defined, then build a list of default columns and
        # let the declared columns override them.
        if opts.model:
            columns = columns_for_model(opts.model, opts.columns, opts.exclude)
            columns.update(self.declared_columns)
            self.base_columns = columns
        return self


class ModelTable(BaseTable):
    """Table that is based on a model.

    Similar to ModelForm, a column will automatically be created for all
    the model's fields. You can modify this behaviour with a inner Meta
    class:

        class MyTable(ModelTable):
            class Meta:
                model = MyModel
                exclude = ['fields', 'to', 'exclude']
                fields = ['fields', 'to', 'include']

    One difference to a normal table is the initial data argument. It can
    be a queryset or a model (it's default manager will be used). If you
    just don't any data at all, the model the table is based on will
    provide it.
    """

    __metaclass__ = ModelTableMetaclass

    rows_class = ModelRows

    def __init__(self, data=None, *args, **kwargs):
        if data == None:
            if self._meta.model is None:
                raise ValueError('Table without a model association needs '
                    'to be initialized with data')
            self.queryset = self._meta.model._default_manager.all()
        elif hasattr(data, '_default_manager'): # saves us db.models import
            self.queryset = data._default_manager.all()
        else:
            self.queryset = data

        super(ModelTable, self).__init__(self.queryset, *args, **kwargs)

    def _validate_column_name(self, name, purpose):
        """Overridden. Only allow model-based fields and valid model
        spanning relationships to be sorted."""

        # let the base class sort out the easy ones
        result = super(ModelTable, self)._validate_column_name(name, purpose)
        if not result:
            return False

        if purpose == 'order_by':
            column = self.columns[name]

            # "data" can really be used in two different ways. It is
            # slightly confusing and potentially should be changed.
            # It can either refer to an attribute/field which the table
            # column should represent, or can be a callable (or a string
            # pointing to a callable attribute) that is used to render to
            # cell. The difference is that in the latter case, there may
            # still be an actual source model field behind the column,
            # stored in "declared_name". In other words, we want to filter
            # out column names that are not oderable, and the column name
            # we need to check may either be stored in "data" or in
            # "declared_name", depending on if and what kind of value is
            # in "data". This is the reason why we try twice.
            #
            # See also bug #282964.
            #
            # TODO: It might be faster to try to resolve the given name
            # manually recursing the model metadata rather than
            # constructing a queryset.
            for lookup in (column.column.data, column.declared_name):
                if not lookup or callable(lookup):
                    continue
                try:
                    # Let Django validate the lookup by asking it to build
                    # the final query; the way to do this has changed in
                    # Django 1.2, and we try to support both versions.
                    _temp = self.queryset.order_by(lookup).query
                    if hasattr(_temp, 'as_sql'):
                        _temp.as_sql()
                    else:
                        from django.db import DEFAULT_DB_ALIAS
                        _temp.get_compiler(DEFAULT_DB_ALIAS).as_sql()
                    break
                except FieldError:
                    pass
            else:
                return False

        # if we haven't failed by now, the column should be valid
        return True

    def _build_snapshot(self):
        """Overridden. The snapshot in this case is simply a queryset
        with the necessary filters etc. attached.
        """

        # reset caches
        self._columns._reset()
        self._rows._reset()

        queryset = self.queryset
        if self.order_by:
            actual_order_by = self._resolve_sort_directions(self.order_by)
            queryset = queryset.order_by(*self._cols_to_fields(actual_order_by))
        return queryset
