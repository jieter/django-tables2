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

CSS
---

If you want to affect the appearance of the table using CSS, you probably want
to add a ``class`` or ``id`` attribute to the ``<table>`` element. This can be
achieved by specifying an ``attrs`` variable in the table's ``Meta`` class.

.. code-block:: python

    >>> import django_tables as tables
    >>> class SimpleTable(tables.Table):
    ...     id = tables.Column()
    ...     age = tables.Column()
    ...
    ...     class Meta:
    ...         attrs = {'class': 'mytable'}
    ...
    >>> table = SimpleTable()
    >>> table.as_html()
    '<table class="mytable">...'

The :attr:`Table.attrs` property actually returns an :class:`AttributeDict`
object. These objects are identical to :class:`dict`, but have an
:meth:`AttributeDict.as_html` method that returns a HTML tag attribute string.

.. code-block:: python

    >>> from django_tables.utils import AttributeDict
    >>> attrs = AttributeDict({'class': 'mytable', 'id': 'someid'})
    >>> attrs.as_html()
    'class="mytable" id="someid"'

The returned string is marked safe, so it can be used safely in a template.

Column formatter
----------------

Using a formatter is a quick way to adjust the way values are displayed in a
column. A limitation of this approach is that you *only* have access to a
single attribute of the data source.

To use a formatter, simply provide the :attr:`~Column.formatter` argument to a
:class:`Column` when you define the :class:`Table`:

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

As you can see, the only the value of the column is available to the formatter.
This means that **it's impossible create a formatter that incorporates other
values of the record**, e.g. a column with an ``<a href="...">`` that uses
:func:`reverse` with the record's ``pk``.

If formatters aren't powerful enough, you'll need to either :ref:`create a
Column subclass <subclassing-column>`, or to use the
:ref:`Table.render_FOO method <table.render_foo>`.

.. _table.render_foo:

.. _table.render_foo:

:meth:`Table.render_FOO` Method
-------------------------------

This approach provides a lot of control, but is only suitable if you intend to
customise the rendering for a single table (otherwise you'll end up having to
copy & paste the method to every table you want to modify – which violates
DRY).

The example below has a number of different techniques in use:

* :meth:`Column.render` (accessible via :attr:`BoundColumn.column`) applies the
  *formatter* if it's been provided. The effect of this behaviour can be seen
  below in the output for the ``id`` column. Square brackets (from the
  *formatter*) have been applied *after* the angled brackets (from the
  :meth:`~Table.render_FOO`).
* Completely abitrary values can be returned by :meth:`render_FOO` methods, as
  shown in :meth:`~SimpleTable.render_row_number` (a :attr:`_counter` attribute
  is added to the :class:`SimpleTable` object to keep track of the row number).

  This is possible because :meth:`render_FOO` methods override the default
  behaviour of retrieving a value from the data-source.

.. code-block:: python

    >>> import django_tables as tables
    >>> class SimpleTable(tables.Table):
    ...     row_number = tables.Column()
    ...     id = tables.Column(formatter=lambda x: '[%s]' % x)
    ...     age = tables.Column(formatter=lambda x: '%d years old' % x)
    ...
    ...     def render_row_number(self, bound_column, bound_row):
    ...         value = getattr(self, '_counter', 0)
    ...         self._counter = value + 1
    ...         return 'Row %d' % value
    ...
    ...     def render_id(self, bound_column, bound_row):
    ...         value = bound_column.column.render(table=self,
    ...                                            bound_column=bound_column,
    ...                                            bound_row=bound_row)
    ...         return '<%s>' % value
    ...
    >>> table = SimpleTable([{'age': 31, 'id': 10}, {'age': 34, 'id': 11}])
    >>> for cell in table.rows[0]:
    ...     print cell
    ...
    Row 0
    <[10]>
    31 years old

The :meth:`Column.render` method is what actually performs the lookup into a
record to retrieve the column value. In the example above, the
:meth:`render_row_number` never called :meth:`Column.render` and as a result
there was not attempt to access the data source to retrieve a value.


Custom Template
---------------

And of course if you want full control over the way the table is rendered,
ignore the built-in generation tools, and instead pass an instance of your
:class:`Table` subclass into your own template, and render it yourself:

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


.. _subclassing-column:

Subclassing :class:`Column`
---------------------------

If you want to have a column behave the same way in many tables, it's best to
create a subclass of :class:`Column` and use that when defining the table.

To change the way cells are rendered, simply override the
:meth:`~Column.render` method.

.. code-block:: python

    >>> import django_tables as tables
    >>>
    >>> class AngryColumn(tables.Column):
    ...     def render(self, *args, **kwargs):
    ...         raw = super(AngryColumn, self).render(*args, **kwargs)
    ...         return raw.upper()
    ...
    >>> class Example(tables.Table):
    ...     normal = tables.Column()
    ...     angry = AngryColumn()
    ...
    >>> data = [{
    ...     'normal': 'May I have some food?',
    ...     'angry': 'Give me the food now!',
    ... }, {
    ...     'normal': 'Hello!',
    ...     'angry': 'What are you looking at?',
    ... }]
    ...
    >>> table = Example(data)
    >>> table.as_html()
    u'<table><thead><tr><th>Normal</th><th>Angry</th></tr></thead><tbody><tr><td>May I have some food?</td><td>GIVE ME THE FOOD NOW!</td></tr><tr><td>Hello!</td><td>WHAT ARE YOU LOOKING AT?</td></tr></tbody></table>\n'

Which, when displayed in a browser, would look something like this:

+-----------------------+--------------------------+
| Normal                | Angry                    |
+=======================+==========================+
| May I have some food? | GIVE ME THE FOOD NOW!    |
+-----------------------+--------------------------+
| Hello!                | WHAT ARE YOU LOOKING AT? |
+-----------------------+--------------------------+


If you plan on returning HTML from a :meth:`~Column.render` method, you must
remember to mark it as safe (otherwise it will be escaped when the table is
rendered). This can be achieved by using the :func:`mark_safe` function.

.. code-block:: python

    >>> from django.utils.safestring import mark_safe
    >>>
    >>> class ImageColumn(tables.Column):
    ...     def render(self, **kwargs):
    ...         raw = super(AngryColumn, self).render(**kwargs)
    ...         return mark_safe('<img src="/media/img/%s.jpg" />' % raw)
    ...



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


API Reference
=============

:class:`Table` Objects:
------------------------

.. autoclass:: django_tables.tables.Table
    :members:


:class:`TableOptions` Objects:
------------------------------

.. autoclass:: django_tables.tables.TableOptions
    :members:


:class:`Column` Objects:
------------------------

.. autoclass:: django_tables.columns.Column
    :members: __init__, default, render


:class:`Columns` Objects
------------------------

.. autoclass:: django_tables.columns.Columns
    :members: __init__, all, items, names, sortable, visible, __iter__,
              __contains__, __len__, __getitem__


:class:`BoundColumn` Objects
----------------------------

.. autoclass:: django_tables.columns.BoundColumn
    :members: __init__, table, column, name, accessor, default, formatter,
              sortable, verbose_name, visible


:class:`Rows` Objects
---------------------

.. autoclass:: django_tables.rows.Rows
    :members: __init__, all, page, __iter__, __len__, count, __getitem__


:class:`BoundRow` Objects
-------------------------

.. autoclass:: django_tables.rows.BoundRow
    :members: __init__, __getitem__, __contains__, __iter__, record, table


:class:`AttributeDict` Objects
------------------------------

.. autoclass:: django_tables.utils.AttributeDict
    :members:


:class:`OrderBy` Objects
------------------------

.. autoclass:: django_tables.utils.OrderBy
    :members:


:class:`OrderByTuple` Objects
-----------------------------

.. autoclass:: django_tables.utils.OrderByTuple
    :members: __contains__, __getitem__, __unicode__


Glossary
========

.. glossary::

    table
        The traditional concept of a table. i.e. a grid of rows and columns
        containing data.
