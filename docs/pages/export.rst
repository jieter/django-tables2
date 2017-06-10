.. _export:

Exporting table data
====================

.. versionadded:: 1.8.0

If you want to allow exporting the data present in your django-tables2 tables to various
formats, you must install the `tablib <http://docs.python-tablib.org/en/latest/>`_ package::

    pip install tablib


Adding ability to export the table data to a class based views looks like this::

    import django_tables2 as tables
    from django_tables2.export.views import ExportMixin

    from .models import Person
    from .tables import MyTable

    class TableView(ExportMixin, tables.SingleTableView):
        table_class = MyTable
        model = Person
        template_name = 'django_tables2/bootstrap.html'


Now, if you append ``_report=csv`` to the querystring, the browser will download
a csv file containing your data. Supported export formats are:

    csv, json, latex, ods, tsv, xls, xlsx, yml

If you must use a function view, you might use someting like this::

    from django_tables2.config import RequestConfig
    from django_tables2.export.export import TableExport

    from .models import Person
    from .tables import MyTable

    def table_view(request):
        table = MyTable(Person.objects.all())

        RequestConfig(request).configure(table)

        export_format = request.GET.get('_export', None)
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, table)
            return exporter.response('table.{}'.format(export_format))

        return render(request, 'table.html', {
            'table': table
        })
