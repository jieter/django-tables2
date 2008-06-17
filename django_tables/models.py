from django.utils.datastructures import SortedDict
from tables import BaseTable, DeclarativeColumnsMetaclass, Column, BoundRow

__all__ = ('BaseModelTable', 'ModelTable')

class ModelTableOptions(object):
    def __init__(self, options=None):
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
        column = Column() # TODO: chose the right column type
        if column:
            field_list.append((f.name, column))
    return SortedDict(field_list)

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

class BaseModelTable(BaseTable):
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
    def __init__(self, data=None, *args, **kwargs):
        if data == None:
            self.queryset = self._meta.model._default_manager.all()
        elif isinstance(data, models.Model):
            self.queryset = data._default_manager.all()
        else:
            self.queryset = data

        super(BaseModelTable, self).__init__(self.queryset, *args, **kwargs)

    def _cols_to_fields(self, names):
        """Utility function. Given a list of column names (as exposed to the
        user), converts overwritten column names to their corresponding model
        field name.

        Supports prefixed field names as used e.g. in order_by ("-field").
        """
        result = []
        for ident in names:
            if ident[:1] == '-':
                name = ident[1:]
                prefix = '-'
            else:
                name = ident
                prefix = ''
            result.append(prefix + self.columns[name].declared_name)
        return result

    def _validate_column_name(self, name, purpose):
        """Overridden. Only allow model-based fields to be sorted."""
        if purpose == 'order_by':
            try:
                decl_name = self.columns[name].declared_name
                self._meta.model._meta.get_field(decl_name)
            except Exception: #TODO: models.FieldDoesNotExist:
                return False
        return super(BaseModelTable, self)._validate_column_name(name, purpose)

    def _build_snapshot(self):
        """Overridden. The snapshot in this case is simply a queryset
        with the necessary filters etc. attached.
        """
        queryset = self.queryset
        if self.order_by:
            queryset = queryset.order_by(*self._cols_to_fields(self.order_by))
        self._snapshot = queryset

    def _get_rows(self):
        for row in self.data:
            yield BoundModelRow(self, row)

class ModelTable(BaseModelTable):
    __metaclass__ = ModelTableMetaclass

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
        boundcol = (name in self.table._columns) \
            and self.table._columns[name]\
            or None

        # If the column has a name override (we know then that is was also
        # used for access, e.g. if the condition is true, then
        # ``boundcol.column.name == name``), we need to make sure we use the
        # declaration name to access the model field.
        if boundcol.column.name:
            name = boundcol.declared_name

        result = getattr(self.data, name, None)
        if result is None:
            if boundcol and boundcol.column.default is not None:
                result = boundcol.column.default
            else:
                raise AttributeError()
        return result