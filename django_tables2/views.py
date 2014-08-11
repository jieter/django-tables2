# coding: utf-8
from __future__ import unicode_literals
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.list import ListView
from .config import RequestConfig


class SingleTableMixin(object):
    """
    Adds a Table object to the context. Typically used with
    `.TemplateResponseMixin`.

    :param        table_class: table class
    :type         table_class: subclass of `.Table`
    :param         table_data: data used to populate the table
    :type          table_data: any compatible data source
    :param context_table_name: name of the table's template variable (default:
                               "table")
    :type  context_table_name: `unicode`
    :param   table_pagination: controls table pagination. If a `dict`, passed as
                               the *paginate* keyword argument to
                               `.RequestConfig`. As such, any non-`False`
                               value enables pagination.

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
        paginate = self.get_table_pagination()  # pylint: disable=E1102
        if paginate is not None:
            options['paginate'] = paginate
        RequestConfig(self.request, **options).configure(table)
        return table

    def get_table_class(self):
        """
        Return the class to use for the table.
        """
        if self.table_class:
            return self.table_class
        raise ImproperlyConfigured("A table class was not specified. Define "
                                   "%(cls)s.table_class"
                                   % {"cls": type(self).__name__})

    def get_context_table_name(self, table):
        """
        Get the name to use for the table's template variable.
        """
        return self.context_table_name or "table"

    def get_table_data(self):
        """
        Return the table data that should be used to populate the rows.
        """
        if self.table_data:
            return self.table_data
        elif hasattr(self, "get_queryset"):
            return self.get_queryset()
        raise ImproperlyConfigured("Table data was not specified. Define "
                                   "%(cls)s.table_data"
                                   % {"cls": type(self).__name__})

    def get_table_pagination(self):
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


class MultiTableMixin(object):
    tables = None

    def get_tables(self):
        if not self.tables:
            raise ImproperlyConfigured("No tables were specified. Define "
                                       "%(cls)s.tables"
                                       % {"cls": type(self).__name__})

        return self.tables

    def get_table(self, table_def):
        options = {}
        table_class = self.get_table_class(table_def)
        table = table_class(self.get_table_data(table_def))
        paginate = self.get_table_pagination(table_def)
        if paginate is not None:
            options['paginate'] = paginate
        RequestConfig(self.request, **options).configure(table)
        return table

    def get_table_class(self, table_def):
        if hasattr(table_def, 'get_table_class'):
            return table_def.get_table_class(self)

        if table_def.table_class:
            return table_def.table_class

        raise ImproperlyConfigured("A table class was not specified. Define "
                                   "%(cls)s.table_class"
                                   % {"cls": type(self).__name__})

    def get_context_table_name(self, table_def):
        if not hasattr(table_def, 'context_table_name'):
            raise ImproperlyConfigured("Table name for template context was "
                                       "not specified. Define "
                                       "%(cls)s.context_table_name"
                                       % {"cls": type(self).__name__})

        return table_def.context_table_name

    def get_table_data(self, table_def):
        if hasattr(table_def, 'get_table_data'):
            return table_def.get_table_data(self)

        if not table_def.table_data:
            return table_def.table_data

        raise ImproperlyConfigured("Table data was not specified. Define "
                                   "%(cls)s.table_data"
                                   % {"cls": type(self).__name__})

    def get_table_pagination(self, table_def):
        if hasattr(table_def, 'table_pagination'):
            return table_def.table_pagination

        return None

    def get_context_data(self, **kwargs):
        context = super(MultiTableMixin, self).get_context_data(**kwargs)

        for table_def_class in self.get_tables():
            table_def = table_def_class()
            table = self.get_table(table_def)
            context[self.get_context_table_name(table_def)] = table

        return context


class SingleTableView(SingleTableMixin, ListView):
    """
    Generic view that renders a template and passes in a `.Table` object.
    """
