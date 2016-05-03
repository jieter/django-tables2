# coding: utf-8
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.views.generic.list import ListView

from .config import RequestConfig


class SingleTableMixin(object):
    """
    Adds a Table object to the context. Typically used with
    `.TemplateResponseMixin`.

    Arguments:
        table_class: subclass of `.Table`
        table_data: data used to populate the table, any compatible data source.
        context_table_name(str): name of the table's template variable (default:
            'table')
        table_pagination (dict): controls table pagination. If a `dict`, passed as
            the *paginate* keyword argument to `.RequestConfig`. As such, any
            Truthy value enables pagination.

    This mixin plays nice with the Django's`.MultipleObjectMixin` by using
    `.get_queryset`` as a fallback for the table data source.
    """
    table_class = None
    table_data = None
    context_table_name = None
    table_pagination = None

    def get_table(self, **kwargs):
        """
        Return a table object to use. The table has automatic support for
        sorting and pagination.
        """
        options = {}
        table_class = self.get_table_class()
        table = table_class(self.get_table_data(), **kwargs)

        paginate = self.get_table_pagination(table)
        if paginate is not None:
            options['paginate'] = paginate

        elif hasattr(self, 'paginate_by') and self.paginate_by is not None:
            # Since ListView knows the concept paginate_by, we use that if no
            # other pagination is configured.
            options['paginate'] = {'per_page': self.paginate_by}

        RequestConfig(self.request, **options).configure(table)
        return table

    def get_table_class(self):
        """
        Return the class to use for the table.
        """
        if self.table_class:
            return self.table_class
        klass = type(self).__name__
        raise ImproperlyConfigured(
            'A table class was not specified. Define {}.table_class'.format(klass)
        )

    def get_context_table_name(self, table):
        """
        Get the name to use for the table's template variable.
        """
        return self.context_table_name or 'table'

    def get_table_data(self):
        """
        Return the table data that should be used to populate the rows.
        """
        if self.table_data is not None:
            return self.table_data
        elif hasattr(self, 'object_list'):
            return self.object_list

        # it seems this is never going to happen because django wil raise
        # ImproperlyConfigured if no model is defined and
        # SingleTableMixin.get_table_class will raise if no table_data was specified...
        # TODO: consider removing
        elif hasattr(self, 'get_queryset'):
            return self.get_queryset()

        klass = type(self).__name__
        raise ImproperlyConfigured(
            'Table data was not specified. Define {}.table_data'.format(klass)
        )

    def get_table_pagination(self, table):
        """
        Returns pagination options: True for standard pagination (default),
        False for no pagination, and a dictionary for custom pagination.
        """
        return self.table_pagination

    def get_context_data(self, **kwargs):
        """
        Overriden version of `.TemplateResponseMixin` to inject the table into
        the template's context.
        """
        context = super(SingleTableMixin, self).get_context_data(**kwargs)
        table = self.get_table()
        context[self.get_context_table_name(table)] = table
        return context


class SingleTableView(SingleTableMixin, ListView):
    """
    Generic view that renders a template and passes in a `.Table` object.
    """
