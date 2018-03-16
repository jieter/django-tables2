# coding: utf-8
from __future__ import unicode_literals

from itertools import count

from django.core.exceptions import ImproperlyConfigured
from django.views.generic.list import ListView

from . import tables
from .config import RequestConfig


class TableMixinBase(object):
    '''
    Base mixin for the Single- and MultiTable class based views
    '''
    context_table_name = 'table'
    table_pagination = None

    def get_context_table_name(self, table):
        '''
        Get the name to use for the table's template variable.
        '''
        return self.context_table_name

    def get_table_pagination(self, table):
        '''
        Returns pagination options: True for standard pagination (default),
        False for no pagination, and a dictionary for custom pagination.
        '''
        paginate = self.table_pagination

        if hasattr(self, 'paginate_by') and self.paginate_by is not None:
            # Since ListView knows the concept paginate_by, we use that if no
            # other pagination is configured.
            paginate = paginate or {}
            paginate['per_page'] = self.paginate_by

        if paginate is None:
            return True

        return paginate


class SingleTableMixin(TableMixinBase):
    '''
    Adds a Table object to the context. Typically used with
    `.TemplateResponseMixin`.

    Attributes:
        table_class: subclass of `.Table`
        table_data: data used to populate the table, any compatible data source.
        context_table_name(str): name of the table's template variable (default:
            'table')
        table_pagination (dict): controls table pagination. If a `dict`, passed as
            the *paginate* keyword argument to `.RequestConfig`. As such, any
            Truthy value enables pagination. (default: enable pagination).

            The `dict` can be used to specify values for arguments for the call to
            `~.tables.Table.paginate`.

            If you want to use a non-standard paginator for example, you can add a key
            `klass` to the dict, containing a custom `Pagintor` class.

    This mixin plays nice with the Django's ``.MultipleObjectMixin`` by using
    ``.get_queryset`` as a fallback for the table data source.
    '''
    table_class = None
    table_data = None

    def get_table_class(self):
        '''
        Return the class to use for the table.
        '''
        if self.table_class:
            return self.table_class
        if self.model:
            return tables.table_factory(self.model)

        raise ImproperlyConfigured(
            'You must either specify {0}.table_class or {0}.model'.format(type(self).__name__)
        )

    def get_table(self, **kwargs):
        '''
        Return a table object to use. The table has automatic support for
        sorting and pagination.
        '''
        table_class = self.get_table_class()
        table = table_class(data=self.get_table_data(), **kwargs)
        return RequestConfig(self.request, paginate=self.get_table_pagination(table)).configure(table)

    def get_table_data(self):
        '''
        Return the table data that should be used to populate the rows.
        '''
        if self.table_data is not None:
            return self.table_data
        elif hasattr(self, 'object_list'):
            return self.object_list
        elif hasattr(self, 'get_queryset'):
            return self.get_queryset()

        klass = type(self).__name__
        raise ImproperlyConfigured(
            'Table data was not specified. Define {}.table_data'.format(klass)
        )

    def get_table_kwargs(self):
        '''
        Return the keyword arguments for instantiating the table.

        Allows passing customized arguments to the table constructor, for example,
        to remove the buttons column, you could define this method in your View::

            def get_table_kwargs(self):
                return {
                    'exclude': ('buttons', )
                }
        '''
        return {}

    def get_context_data(self, **kwargs):
        '''
        Overriden version of `.TemplateResponseMixin` to inject the table into
        the template's context.
        '''
        context = super(SingleTableMixin, self).get_context_data(**kwargs)
        table = self.get_table(**self.get_table_kwargs())
        context[self.get_context_table_name(table)] = table
        return context


class SingleTableView(SingleTableMixin, ListView):
    '''
    Generic view that renders a template and passes in a `.Table` instances.

    Mixes ``.SingleTableMixin`` with ``django.views.generic.list.ListView``.
    '''


class MultiTableMixin(TableMixinBase):
    '''
    Add a list with multiple Table object's to the context. Typically used with
    `.TemplateResponseMixin`.

    The `tables` attribute must be either a list of `.Table` instances or
    classes extended from `.Table` which are not already instantiated. In that
    case, `get_tables_data` must be able to return the tables data, either by
    having an entry containing the data for each table in `tables`, or by
    overriding this method in order to return this data.

    Attributes:
        tables: list of `.Table` instances or list of `.Table` child objects.
        tables_data: if defined, `tables` is assumed to be a list of table
            classes which will be instatiated with the corresponding item from
            this list of `.TableData` instances.
        table_prefix(str): Prefix to be used for each table. The string must
            contain one instance of `{}`, which will be replaced by an integer
            different for each table in the view. Default is 'table_{}-'.
        context_table_name(str): name of the table's template variable (default:
            'tables')

    .. versionadded:: 1.2.3
    '''
    tables = None
    tables_data = None

    table_prefix = 'table_{}-'

    # override context table name to make sense in a multiple table context
    context_table_name = 'tables'

    def get_tables(self):
        '''
        Return an array of table instances containing data.
        '''
        data = self.get_tables_data()

        if data is None:
            if not self.tables:
                klass = type(self).__name__
                raise ImproperlyConfigured(
                    'No tables were specified. Define {}.tables'.format(klass)
                )

            return self.tables
        else:
            if len(data) != len(self.tables):
                klass = type(self).__name__
                raise ImproperlyConfigured(
                    'len({}.tables_data) != len({}.tables)'.format(klass, klass)
                )
            return list(Table(data[i]) for i, Table in enumerate(self.tables))

    def get_tables_data(self):
        '''
        Return an array of table_data that should be used to populate each table
        '''
        return self.tables_data

    def get_context_data(self, **kwargs):
        context = super(MultiTableMixin, self).get_context_data(**kwargs)
        tables = self.get_tables()

        # apply prefixes and execute requestConfig for each table
        table_counter = count()
        for table in tables:
            table.prefix = self.table_prefix.format(next(table_counter))

            RequestConfig(self.request, paginate=self.get_table_pagination(table)).configure(table)

            context[self.get_context_table_name(table)] = list(tables)

        return context
