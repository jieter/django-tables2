# -*- coding: utf-8 -*-
from django.core.exceptions import ImproperlyConfigured
from django.db.models import Q
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
    search_fields = None


    def get_table(self):
        """
        Return a table object to use. The table has automatic support for
        sorting and pagination.
        """
        table_class = self.get_table_class()
        table = table_class(self.get_table_data())
        RequestConfig(self.request).configure(table)
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

    def get_query_string(self):
        return self.request.GET.get('query', None)

    def get_table_data(self):
        """
        Return the table data that should be used to populate the rows.
        """
        if self.table_data:
            return self.table_data
        elif hasattr(self, "get_queryset"):
            qs = self.get_queryset()
            # Build a queryset filter based on search_fields attribute
            # For example setting search_fields = ['name', 'email'] will give:
            # filter(Q(name__icontains=query) | Q(email__icontains=query))
            search_fields = getattr(self, 'search_fields', [])
            q = self.get_query_string()
            if q and search_fields and data:
                queries = [Q(**{ field + '__icontains': q })
                           for field in search_fields]
                query = queries.pop()
                for item in queries:
                    query |= item
                qs = qs.filter(query)
            return qs
        raise ImproperlyConfigured(u"Table data was not specified. Define "
                                   u"%(cls)s.table_data"
                                   % {"cls": type(self).__name__})

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
