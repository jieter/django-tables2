.. _export:

Exporting table data
====================

.. versionadded:: 1.8.0

If you want to allow exporting the data present in your django-tables2 tables to various
formats, you must install the `tablib <https://tablib.readthedocs.io>`_ package::

    pip install tablib

.. note::
   For all supported formats (xls, xlsx, etc.), you must install additional dependencies:
   `Installing tablib: <https://tablib.readthedocs.io/en/stable/install/#installing-tablib`_
   

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

    csv, json, latex, ods, tsv, xls, xlsx, yaml

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


Including and excluding columns
-------------------------------

Some data might be rendered in the HTML version of the table using color coding,
but need a different representation in an export format. Use columns with `visible=False`
to include columns in the export, but not visible in the regular rendering::

    class Table(tables.Table):
        name = columns.Column(exclude_from_export=True)
        first_name = columns.Column(visible=False)
        last_name = columns.Column(visible=False)

Certain columns do not make sense while exporting data: you might show images or
have a column with buttons you want to exclude from the export.
You can define the columns you want to exclude in several ways::

    # exclude a column while defining Columns on a table:
    class Table(tables.Table):
        name = columns.Column()
        buttons = columns.TemplateColumn(template_name="...", exclude_from_export=True)


    # exclude columns while creating the TableExport instance:
    exporter = TableExport("csv", table, exclude_columns=("image", "buttons"))


If you use the ``django_tables2.export.ExportMixin``, add an ``exclude_columns`` attribute to your class::

    class TableView(ExportMixin, tables.SingleTableView):
        table_class = MyTable
        model = Person
        template_name = 'django_tables2/bootstrap.html'
        exclude_columns = ("buttons", )


Tablib Dataset Configuration
----------------------------

django-tables2 uses ``tablib`` to export the table data.
You may pass kwargs to the ``tablib.Dataset`` via the ``TableExport`` constructor ``dataset_kwargs`` parameter::

    exporter = TableExport("xlsx", table, dataset_kwargs={"title": "My Custom Sheet Name"})

Default for ``tablib.Dataset.title`` is based on ``table.Meta.model._meta.verbose_name_plural.title()``, if available.

If you use the ``django_tables2.export.ExportMixin``, simply add a ``dataset_kwargs`` attribute to your class::

    class View(ExportMixin, tables.SingleTableView):
        table_class = MyTable
        model = Person
        dataset_kwargs = {"title": "People"}

or override the ``ExportMixin.get_dataset_kwargs`` method to return the kwargs dictionary dynamically.


Generating export URLs
----------------------
.. note::

    To use ``export_url`` you must first load it in your template::
        
        {% load export_url from django_tables2 %}
    
You can use the ``export_url`` template tag included with django_tables2
to render a link to export the data as ``csv``::

    {% export_url "csv" %}

This will make sure any other query string parameters will be preserved, for example
in combination when filtering table items.

If you want to render more than one button, you could use something like this::

    {% for format in view.export_formats %}
        <a href="{% export_url format %}">
            download  <code>.{{ format }}</code>
        </a>
    {% endfor %}

.. note::

    This example assumes you define a list of possible
    export formats on your view instance in attribute ``export_formats``.
