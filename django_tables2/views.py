# coding: utf-8
from __future__ import unicode_literals
from django.core.exceptions import ImproperlyConfigured
from django.views.generic import ListView, TemplateView
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


class SingleTableView(SingleTableMixin, ListView):
    """
    Generic view that renders a template and passes in a `.Table` object.
    """


class MultiTableMixin(object):
    """
    Adds multiple Table objects to the context. Typically used with
    `.TemplateResponseMixin`. Table pagination is not supported.

    :param       table_classes: valuees are table classes
    :type        table_classes: dict of table_id -> `.Table`
    :param          table_data: data used to populate the table
    :type           table_data: dict of table_id -> compatible data source
    :param        table_models: models of objects to use in table, if no
                                "get_<table_id>_queryset" method is defined
    :type         table_models: dict of table_id -> `.Model`
    :param context_table_names: name of the table's template variable
                                (default: "<table_id>_table")
    :type  context_table_names: dict of table_id -> `unicode`
    """
    table_classes = {}
    table_data = {}
    table_models = {}
    context_table_names = {}

    def get_tables(self):
        """
        Return a dict of table objects to use.
        """
        table_classes = self.get_table_classes()
        tables = {}
        for table_id, table_class in table_classes.iteritems():
            table = table_class(self.get_table_data(table_id))
            tables[table_id] = table
        return tables

    def get_table_classes(self):
        """
        Return the classes to use for the tables.
        """
        if self.table_classes:
            return self.table_classes
        raise ImproperlyConfigured(u"Table classes were not specified. Define "
                                   u"%(cls)s.table_classes"
                                   % {"cls": type(self).__name__})

    def get_context_table_name(self, table_id):
        """
        Get the name to use for the table's template variable.
        """
        default = '%s_table' % table_id
        return self.context_table_names.get(table_id, default)

    def get_table_data(self, table_id):
        """
        Return the table data that should be used to populate the rows.
        """
        if table_id in self.table_data:
            return self.table_data[table_id]
        if hasattr(self, 'get_%s_queryset' % table_id):
            return getattr(self, 'get_%s_queryset' % table_id)()
        if table_id in self.table_models:
            return self.table_models[table_id].objects.all()
        raise ImproperlyConfigured(u"Table data for %(table_id)s not specified. "
                                   u"Define %(cls)s.table_data[%(table_id)s], "
                                   u"%(cls)s.get_%(table_id)s_queryset(), or "
                                   u"%(cls)s.table_models[%(table_id)s]."
                                   % {
                                       "cls": type(self).__name__,
                                       "table_id": table_id,
                                   })

    def get_context_data(self, **kwargs):
        """
        Overriden version of `.TemplateResponseMixin` to inject the table into
        the template's context.
        """
        context = super(MultiTableMixin, self).get_context_data(**kwargs)
        tables = self.get_tables()
        context.update(dict(
            (self.get_context_table_name(table_id), table)
            for table_id, table in tables.iteritems()
        ))
        return context


class MultiTableView(MultiTableMixin, TemplateView):
    """
    Generic view that renders a template and passes in a set of
    `.Table` objects.
    """
