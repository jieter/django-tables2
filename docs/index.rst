==========================================
django-tables - A Django Queryset renderer
==========================================


``django-tables`` wants to help you present data while allowing your user
to apply common tabular transformations on it.

Currently, this mostly mostly means "sorting", i.e. parsing a query string
coming from the browser (while supporting multiple sort fields, restricting
the fields that may be sorted, exposing fields under different names) and
generating the proper links to allow the user to change the sort order.

In the future, filtering and grouping will hopefully be added.


A simple example
----------------

The API looks similar to that of Django's ``ModelForms``:

.. code-block:: python

    import django_tables as tables

    class CountryTable(tables.MemoryTable):
        name = tables.Column(verbose_name="Country Name")
        population = tables.Column(sortable=False, visible=False)
        time_zone = tables.Column(name="tz", default="UTC+1")

Instead of fields, you declare a column for every piece of data you want
to expose to the user.

To use the table, create an instance:

.. code-block:: python

    countries = CountryTable([{'name': 'Germany', population: 80},
                              {'name': 'France', population: 64}])

Decide how the table should be sorted:

.. code-block:: python

    countries.order_by = ('name',)
    assert [row.name for row in countries.row] == ['France', 'Germany']

    countries.order_by = ('-population',)
    assert [row.name for row in countries.row] == ['Germany', 'France']

If you pass the table object along into a template, you can do:

.. code-block:: django

    {% for column in countries.columns %}
        {{ column }}
    {% endfor %}

Which will give you:

.. code-block:: django

    Country Name
    Timezone

Note that ``population`` is skipped (as it has ``visible=False``), that the
declared verbose name for the ``name`` column is used, and that ``time_zone``
is converted into a more beautiful string for output automatically.


Common Workflow
~~~~~~~~~~~~~~~

Usually, you are going to use a table like this. Assuming ``CountryTable``
is defined as above, your view will create an instance and pass it to the
template:

.. code-block:: python

    def list_countries(request):
        data = ...
        countries = CountryTable(data, order_by=request.GET.get('sort'))
        return render_to_response('list.html', {'table': countries})

Note that we are giving the incoming ``sort`` query string value directly to
the table, asking for a sort. All invalid column names will (by default) be
ignored. In this example, only ``name`` and ``tz`` are allowed, since:

 * ``population`` has ``sortable=False``
 * ``time_zone`` has it's name overwritten with ``tz``.

Then, in the ``list.html`` template, write:

.. code-block:: django

    <table>
    <tr>
        {% for column in table.columns %}
        <th><a href="?sort={{ column.name_toggled }}">{{ column }}</a></th>
        {% endfor %}
    </tr>
    {% for row in table.rows %}
        <tr>
        {% for value in row %}
            <td>{{ value }}</td>
        {% endfor %}
        </tr>
    {% endfor %}
    </table>

This will output the data as an HTML table. Note how the table is now fully
sortable, since our link passes along the column name via the querystring,
which in turn will be used by the server for ordering. ``order_by`` accepts
comma-separated strings as input, and ``{{ column.name_toggled }}`` will be
rendered as a such a string.

Instead of the iterator, you can alos use your knowledge of the table
structure to access columns directly:

.. code-block:: django

    {% if table.columns.tz.visible %}
        {{ table.columns.tz }}
    {% endfor %}


In Detail
=========

.. toctree::
   :maxdepth: 2

   installation
   types/index
   features/index
   columns
   templates

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

