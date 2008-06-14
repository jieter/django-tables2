from django.utils.datastructures import SortedDict
from tables import BaseTable, DeclarativeColumnsMetaclass, Column

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
        column = Column()
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

class ModelDataProxy(object):
    pass

class BaseModelTable(BaseTable):
    def __init__(self, data, *args, **kwargs):
        super(BaseModelTable, self).__init__([], *args, **kwargs)
        if isinstance(data, models.Model):
            self.queryset = data._meta.default_manager.all()
        else:
            self.queryset = data

    def _get_data(self):
        """Overridden. Return a proxy object so we don't need to load the
        complete queryset.
        # TODO: we probably simply want to build the queryset
        """
        if self._data_cache is None:
            self._data_cache = ModelDataProxy(self.queryset)
        return self._data_cache

class ModelTable(BaseModelTable):
    __metaclass__ = ModelTableMetaclass
