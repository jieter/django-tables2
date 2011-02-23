.. default-domain:: py

=====================================================
django-tables - An app for creating HTML tables
=====================================================

django-tables simplifies the task of turning sets of datainto HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
``django.forms`` does for HTML forms.

Quick start guide
=================

1. Download and install the package.
2. Install the tables framework by adding ``'django_tables'`` to your
   ``INSTALLED_APPS`` setting.
3. Ensure that ``'django.core.context_processors.request'`` is in your
   ``TEMPLATE_CONTEXT_PROCESSORS`` setting.
4. Write table classes for the types of tables you want to display.
5. Create an instance of a table in a view, provide it your data, and pass it
   to a template for display.
6. Use ``{{ table.as_html }}``, the
   :ref:`template tag <template_tags.render_table>`, or your own
   custom template code to display the table.


Tables
======

For each type of table you want to display, you will need to create a subclass
of ``django_tables.Table`` that describes the structure of the table.

In this example we are going to take some data describing three countries and
turn it into a HTML table. We start by creating our data:

.. code-block:: python

    >>> countries = [
    ...     {'name': 'Australia', 'population': 21, 'tz': 'UTC +10', 'visits': 1},
    ...     {'name': 'Germany', 'population', 81, 'tz': 'UTC +1', 'visits': 2},
    ...     {'name': 'Mexico', 'population': 107, 'tz': 'UTC -6', 'visits': 0},
    ... ]

Next we subclass ``django_tables.Table`` to create a table that describes our
data. The API should look very familiar since it's based on Django's
database model API:

.. code-block:: python

    >>> import django_tables as tables
    >>> class CountryTable(tables.Table):
    ...     name = tables.Column()
    ...     population = tables.Column()
    ...     tz = tables.Column(verbose_name='Time Zone')
    ...     visits = tables.Column()


Providing data
--------------

To use the table, simply create an instance of the table class and pass in your
data. e.g. following on from the above example:

.. code-block:: python

    >>> table = CountryTable(countries)

Tables have support for any iterable data that contains objects with
attributes that can be accessed as property or dictionary syntax:

.. code-block:: python

    >>> table = SomeTable([{'a': 1, 'b': 2}, {'a': 4, 'b': 8}])  # valid
    >>> table = SomeTable(SomeModel.objects.all())  # also valid

Each item in the data corresponds to one row in the table. By default, the
table uses column names as the keys (or attributes) for extracting cell values
from the data. This can be changed by using the :attr:`~Column.accessor`
argument.


Displaying a table
------------------

There are two ways to display a table, the easiest way is to use the table's
own ``as_html`` method:

.. code-block:: django

    {{ table.as_html }}

Which will render something like:

+--------------+------------+---------+
| Country Name | Population | Tz      |
+==============+============+=========+
| Australia    | 21         | UTC +10 |
+--------------+------------+---------+
| Germany      | 81         | UTC +1  |
+--------------+------------+---------+
| Mexico       | 107        | UTC -6  |
+--------------+------------+---------+

The downside of this approach is that pagination and sorting will not be
available. These features require the use of the ``{% render_table %}``
template tag:

.. code-block:: django

    {% load django_tables %}
    {% render_table table %}

See :ref:`template_tags` for more information.


Ordering
--------

Controlling the order that the rows are displayed (sorting) is simple, just use
the :attr:`~Table.order_by` property or pass it in when initialising the
instance:

.. code-block:: python

    >>> # order_by argument when creating table instances
    >>> table = CountryTable(countries, order_by='name, -population')
    >>> table = CountryTable(countries, order_by=('name', '-population'))
    >>> # order_by property on table instances
    >>> table = CountryTable(countries)
    >>> table.order_by = 'name, -population'
    >>> table.order_by = ('name', '-population')


Customising the output
======================

There are a number of options available for changing the way the table is
rendered. Each approach provides balance of ease-of-use and control (the more
control you want, the less easy it is to use).


Column formatter
----------------

If all you want to do is change the way a column is formatted, you can simply
provide the :attr:`~Column.formatter` argument to a :class:`Column` when you
define the :class:`Table`:

.. code-block:: python

    >>> import django_tables as tables
    >>> class SimpleTable(tables.Table):
    ...     id = tables.Column(formatter=lambda x: '#%d' % x)
    ...     age = tables.Column(formatter=lambda x: '%d years old' % x)
    ...
    >>> table = SimpleTable([{'age': 31, 'id': 10}, {'age': 34, 'id': 11}])
    >>> row = table.rows[0]
    >>> for cell in row:
    ...     print cell
    ...
    #10
    31 years old

The limitation of this approach is that you're unable to incorporate any
run-time information of the table into the formatter. For example it would not
be possible to incorporate the row number into the cell's value.


Column render method
--------------------

This approach provides a lot of control, but is only suitable if you intend to
customise the rendering for a single table (otherwise you'll end up having to
copy & paste the method to every table you want to modify – which violates
DRY).

    >>> import django_tables as tables
    >>> class SimpleTable(tables.Table):
    ...     row_number = tables.Column()
    ...     id = tables.Column(formatter=lambda x: '#%d' % x)
    ...     age = tables.Column(formatter=lambda x: '%d years old' % x)
    ...
    ...     def render_row_number(self, bound_column, bound_row):
    ...         value =
    ...
    ...     def render_id(self, bound_column, bound_row):
    ...         value = self.column.
    ...
    >>> table = SimpleTable([{'age': 31, 'id': 10}, {'age': 34, 'id': 11}])
    >>> for cell in table.rows[0]:
    ...     print cell
    ...
    #10
    31 years old

If you want full control over the way the table is rendered, create
and render the template yourself:

.. code-block:: django

    {% load django_tables %}
    <table>
        <thead>
            <tr>
            {% for column in table.columns %}
                <th><a href="{% set_url_param sort=column.name_toggled %}">{{ column }}</a></th>
            {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in table.rows %}
            <tr>
                {% for cell in row %}
                    <td>{{ cell }}</td>
                {% endfor %}
            </tr>
            {% endfor %}
        </tbody>
    </table>



:class:`Columns` Objects
========================

.. autoclass:: django_tables.columns.Columns
    :members: __init__, all, items, names, sortable, visible, __iter__,
              __contains__, __len__, __getitem__


:class:`BoundColumn` Objects
============================

.. autoclass:: django_tables.columns.BoundColumn
    :members: __init__, table, column, name, accessor, default, formatter,
              sortable, verbose_name, visible


Column options
--------------

Each column takes a certain set of column-specific arguments.

There's also a set of common arguments available to all column types. All are
optional. Here's a summary of them.

    :attr:`~Column.verbose_name`
        A pretty human readable version of the column name. Typically this is
        used in the header cells in the HTML output.

    :attr:`~Column.accessor`
        A string or callable that specifies the attribute to access when
        retrieving the value for a cell in this column from the data-set.
        Multiple lookups can be achieved by providing a dot separated list of
        lookups, e.g. ``"user.first_name"``. The functionality is identical to
        that of Django's template variable syntax, e.g. ``{{ user.first_name
        }}``

        A callable should be used if the dot separated syntax is not capable of
        describing the lookup properly. The callable will be passed a single
        item from the data (if the table is using :class:`QuerySet` data, this
        would be a :class:`Model` instance), and is expected to return the
        correct value for the column.

        Consider the following:

        .. code-block:: python

            >>> import django_tables as tables
            >>> data = [
            ...     {'dot.separated.key': 1},
            ...     {'dot.separated.key': 2},
            ... ]
            ...
            >>> class SlightlyComplexTable(tables.Table):
            >>>     dot_seperated_key = tables.Column(accessor=lambda x: x['dot.separated.key'])
            ...
            >>> table = SlightlyComplexTable(data)
            >>> for row in table.rows:
            >>>     print row['dot_seperated_key']
            ...
            1
            2

        This would not have worked:

        .. code-block:: python

            dot_seperated_key = tables.Column(accessor='dot.separated.key')

    :attr:`~Column.default`
        The default value for the column. This can be a value or a callable
        object [1]_. If an object in the data provides :const:`None` for a
        column, the default will be used instead.

        The default value may affect ordering, depending on the type of
        data the table is using. The only case where ordering is not affected
        ing when a :class:`QuerySet` is used as the table data (since sorting
        is performed by the database).

        .. [1] The provided callable object must not expect to receive any
           arguments.

    :attr:`~Column.visible`
        If :const:`False`, this column will not be in the HTML output.

        When a field is not visible, it is removed from the table's
        :attr:`~Column.columns` iterable.

    :attr:`~Column.sortable`
        If :const:`False`, this column will not be allowed to be used in
        ordering the table.

    :attr:`~Column.formatter`
        A callable object that is used as a final step in formatting the value
        for a cell. The callable will be passed the string that would have
        otherwise been displayed in the cell.


Rows
====

:class:`Rows` Objects
=====================

.. autoclass:: django_tables.rows.Rows
    :members: __init__, all, page, __iter__, __len__, count, __getitem__


:class:`BoundRow` Objects
=========================

.. autoclass:: django_tables.rows.BoundRow
    :members: __init__, values, __getitem__, __contains__, __iter__


.. _template_tags:

Template tags
=============

.. _template_tags.render_table:

render_table
------------

If you want to render a table that provides support for sorting and pagination,
you must use the ``{% render_table %}`` template tag. In this example ``table``
is an instance of a :class:`django_tables.Table` that has been put into the
template context:

.. code-block:: django

    {% load django_tables %}
    {% render_table table %}


.. _template_tags.set_url_param:

set_url_param
-------------

This template tag is a utility that allows you to update a portion of the
query-string without overwriting the entire thing. However you shouldn't need
to use this template tag unless you are rendering the table from scratch (i.e.
not using ``as_html()`` or ``{% render_table %}``).

This is very useful if you want the give your users the ability to interact
with your table (e.g. change the ordering), because you will need to create
urls with the appropriate queries.

Let's assume we have the query-string
``?search=pirates&sort=name&page=5`` and we want to update the ``sort``
parameter:

.. code-block:: django

    {% set_url_param sort="dob" %}         # ?search=pirates&sort=dob&page=5
    {% set_url_param sort="" %}            # ?search=pirates&page=5
    {% set_url_param sort="" search="" %}  # ?page=5



A table instance bound to data has two attributes ``columns`` and ``rows``,
which can be iterated over:

.. code-block:: django

    <table>
        <thead>
            <tr>
            {% for column in table.columns %}
                <th><a href="?sort={{ column.name_toggled }}">{{ column }}</a></th>
            {% endfor %}
            </tr>
        </thead>
        <tbody>
        {% for row in table.rows %}
            <tr>
            {% for value in row %}
                <td>{{ value }}</td>
            {% endfor %}
            </tr>
        {% endfor %}
        </tbody>
    </table>
