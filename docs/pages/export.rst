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
        template_name = "django_tables2/bootstrap.html"


Now, if you append ``_export=csv`` to the query string, the browser will download
a csv file containing your data. Supported export formats are:

    csv, json, latex, ods, tsv, xls, xlsx, yml

To customize the name of the query parameter add an ``export_trigger_param``
attribute to your class.

By default, the file will be named ``table.ext``, where ``ext`` is the requested
export format extension. To customize this name, add a ``export_name`` attribute
to your class. The correct extension will be appended automatically to this value.

If you must use a function view, you might use something like this::

    from django_tables2.config import RequestConfig
    from django_tables2.export.export import TableExport

    from .models import Person
    from .tables import MyTable

    def table_view(request):
        table = MyTable(Person.objects.all())

        RequestConfig(request).configure(table)

        export_format = request.GET.get("_export", None)
        if TableExport.is_valid_format(export_format):
            exporter = TableExport(export_format, table)
            return exporter.response("table.{}".format(export_format))

        return render(request, "table.html", {
            "table": table
        })

What exactly is exported?
-------------------------

The export views use the `.Table.as_values()` method to get the data from the table.
Because we often use HTML in our table cells, we need to specify something else for the
export to make sense.

If you use :ref:`table.render_foo`-methods to customize the output for a column,
you should define a :ref:`table.value_foo`-method, returning the value you want
to be exported.

If you are creating your own custom columns, you should know that each column
defines a `value()` method, which is used in `Table.as_values()`.
By default, it just calls the `render()` method on that column.
If your custom column produces HTML, you should override this method and return
the actual value.


Excluding columns
-----------------

Certain columns do not make sense while exporting data: you might show images or
have a column with buttons you want to exclude from the export.
You can define the columns you want to exclude in several ways::

    # exclude a column while defining Columns on a table:
    class Table(tables.Table):
        name = columns.Column()
        buttons = columns.TemplateColumn(template_name="...", exclude_from_export=True)


    # exclude columns while creating the TableExport instance:
    exporter = TableExport("csv", table, exclude_columns=("image", "buttons"))


If you use the ``~.ExportMixin``, add an ``exclude_columns`` attribute to your class::

    class TableView(ExportMixin, tables.SingleTableView):
        table_class = MyTable
        model = Person
        template_name = 'django_tables2/bootstrap.html'
        exclude_columns = ("buttons", )


Generating export URLs
----------------------

You can use the ``querystring`` template tag included with django_tables2
to render a link to export the data as ``csv``::

    {% export_url "csv" %}

This will make sure any other query string parameters will be preserved, for example
in combination when filtering table items.

If you want to render more than one button, you could use something like this::

    {% for format in table.export_formats %}
        <a href="{% export_url format %}">
            download  <code>.{{ format }}</code>
        </a>
    {% endfor %}

.. note::

    This example assumes you define a list of possible
    export formats on your table instance in attribute ``export_formats``
