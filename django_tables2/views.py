# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import TemplateResponseMixin
from django.views.generic.list import ListView
from .config import RequestConfig


class SingleTableMixin(object):
    """
    Adds a Table object to the context. Typically used with
    ``TemplateResponseMixin``.

    :param table_class: table class
    :type table_class: subclass of ``django_tables2.Table``

    :param table_data: data used to populate the table
    :type table_data: any compatible data source

    :param context_table_name: name of the table's template variable (default:
        "table")
    :type context_table_name: ``string``

    This mixin plays nice with the Django's ``MultipleObjectMixin`` by using
    ``get_queryset()`` as a fallback for the table data source.
    """
    table_class = None
    table_data = None
    context_table_name = None
    table_pagination = None

    def get_table(self):
        """
        Return a table object to use. The table has automatic support for
        sorting and pagination.
        """
        options = {}
        table_class = self.get_table_class()
        table = table_class(self.get_table_data())
        paginate = self.get_table_pagination()
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
        raise ImproperlyConfigured(u"A table class was not specified. Define "
                                   u"%(cls)s.table_class"
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
        raise ImproperlyConfigured(u"Table data was not specified. Define "
                                   u"%(cls)s.table_data"
                                   % {"cls": type(self).__name__})
            
    def get_table_pagination(self):
        """
        Returns pagination options: True for standard pagination (default),
        False for no pagination, and a dictionary for custom pagination.
        """
        return self.table_pagination

    def get_context_data(self, **kwargs):
        """
        Overriden version of ``TemplateResponseMixin`` to inject the table into
        the template's context.
        """
        context = super(SingleTableMixin, self).get_context_data(**kwargs)
        table = self.get_table()
        context[self.get_context_table_name(table)] = table
        return context


class SingleTableView(SingleTableMixin, ListView):
    """
    Generic view that renders a template and passes in a ``Table`` object.
    """
