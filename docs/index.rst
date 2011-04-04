.. default-domain:: py

===============================================
django-tables - An app for creating HTML tables
===============================================

django-tables simplifies the task of turning sets of datainto HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
``django.forms`` does for HTML forms.

Quick start guide
=================

1. Download and install from https://github.com/bradleyayers/django-tables.
   Grab a ``.tar.gz`` of the latest tag, and run ``pip install <tar.gz>``.
2. Hook the app into your Django project by adding ``'django_tables'`` to your
   ``INSTALLED_APPS`` setting.
3. Write a subclass of :class:`~django_tables.tables.Table` that describes the
   structure of your table.
4. Create an instance of your table in a :term:`view`, provide it with
   :term:`table data`, and pass it to a :term:`template` for display.
5. Use ``{{ table.as_html }}``, the
   :ref:`template tag <template-tags.render_table>`, or your own
   :ref:`custom template <custom-template>` to display the table.


Slow start guide
================

We're going to take some data that describes three countries and
turn it into an HTML table. This is the data we'll be using:

.. code-block:: python

    countries = [
        {'name': 'Australia', 'population': 21, 'tz': 'UTC +10', 'visits': 1},
        {'name': 'Germany', 'population', 81, 'tz': 'UTC +1', 'visits': 2},
        {'name': 'Mexico', 'population': 107, 'tz': 'UTC -6', 'visits': 0},
    ]


The first step is to subclass :class:`~django_tables.tables.Table` and describe
the table structure. This is done by creating a column for each attribute in
the :term:`table data`.

.. code-block:: python

    import django_tables as tables

    class CountryTable(tables.Table):
        name = tables.Column()
        population = tables.Column()
        tz = tables.Column(verbose_name='Time Zone')
        visits = tables.Column()


Now that we've defined our table, it's ready for use. We simply create an
instance of it, and pass in our table data.

.. code-block:: python

    table = CountryTable(countries)

Now we add it to our template context and render it to HTML. Typically you'd
write a view that would look something like:

.. code-block:: python

    def home(request):
        table = CountryTable(countries)
        return render_to_response('home.html', {'table': table},
                                  context_instances=RequestContext(request))

In your template, the easiest way to :term:`render` the table is via the
:meth:`~django_tables.tables.Table.as_html` method:

.. code-block:: django

    {{ table.as_html }}

…which will render something like:

+--------------+------------+---------+--------+
| Country Name | Population | Tz      | Visit  |
+==============+============+=========+========+
| Australia    | 21         | UTC +10 | 1      |
+--------------+------------+---------+--------+
| Germany      | 81         | UTC +1  | 2      |
+--------------+------------+---------+--------+
| Mexico       | 107        | UTC -6  | 0      |
+--------------+------------+---------+--------+

This approach is easy, but it's not fully featured. For slightly more effort,
you can render a table with sortable columns. For this, you must use the
template tag.

.. code-block:: django

    {% load django_tables %}
    {% render_table table %}

See :ref:`template-tags.render_table` for more information.

The table will be rendered, but chances are it will still look quite ugly. An
easy way to make it pretty is to use the built-in *paleblue* theme. For this to
work, you must add a CSS class to the ``<table>`` tag. This can be achieved by
adding a ``class Meta:`` to the table class and defining a ``attrs`` variable.

.. code-block:: python

    import django_tables as tables

    class CountryTable(tables.Table):
        name = tables.Column()
        population = tables.Column()
        tz = tables.Column(verbose_name='Time Zone')
        visits = tables.Column()

        class Meta:
            attrs = {'class': 'paleblue'}

The last thing to do is to include the stylesheet in the template.

.. code-block:: html

    <link rel="stylesheet" type="text/css" href="{{ STATIC_URL }}django_tables/themes/paleblue/css/screen.css" />

Save your template and reload the page in your browser.


.. _table-data:

Table data
==========

The data used to populate a table is called :term:`table data`. To provide a
table with data, pass it in as the first argument when instantiating a table.

.. code-block:: python

    table = CountryTable(countries)              # valid
    table = CountryTable(Country.objects.all())  # also valid

Each item in the :term:`table data` is called a :term:`record` and is used to
populate a single row in the table. By default, the table uses column names
as :term:`accessors <accessor>` to retrieve individual cell values. This can
be changed via the :attr:`~django_tables.columns.Column.accessor` argument.

Any iterable can be used as table data, and there's builtin support for
:class:`QuerySet` objects (to ensure they're handled effeciently).


.. _ordering:

Ordering
========

Changing the table ordering is easy. When creating a
:class:`~django_tables.tables.Table` object include an `order_by` parameter
with a tuple that describes the way the ordering should be applied.

.. code-block:: python

    table = CountryTable(countries, order_by=('name', '-population'))
    table = CountryTable(countries, order_by='name,-population')  # equivalant

Alternatively, the :attr:`~django_tables.tables.Table.order_by` attribute can
by modified.

    table = CountryTable(countries)
    table.order_by = ('name', '-population')
    table.order_by = 'name,-population'  # equivalant


.. _pagination:

Pagination
==========

Pagination is easy, just call :meth:`.Table.paginate` and pass in the current
page number, e.g.

.. code-block:: python

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        table.paginate(page=request.GET.get('page', 1))
        return render_to_response('people_listing.html', {'table': table},
                                  context_instance=RequestContext(request))

The last set is to render the table. :meth:`.Table.as_html` doesn't support
pagination, so you must use :ref:`{% render_table %}
<template-tags.render_table>`.

.. _custom-rendering:

Custom rendering
================

Various options are available for changing the way the table is :term:`rendered
<render>`. Each approach has a different balance of ease-of-use and
flexibility.

CSS
---

In order to use CSS to style a table, you'll probably want to add a
``class`` or ``id`` attribute to the ``<table>`` element. ``django-tables`` has
a hook that allows abitrary attributes to be added to the ``<table>`` tag.

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

Inspired by Django's ORM, the ``class Meta:`` allows you to define extra
characteristics of a table. See :class:`Table.Meta` for details.

.. _table.render_foo:

.. _table.render_foo:

:meth:`Table.render_FOO` Methods
--------------------------------

If you want to adjust the way table cells in a particular column are rendered,
you can implement a ``render_FOO`` method. ``FOO`` is replaced with the
:term:`name <column name>` of the column.

This approach provides a lot of control, but is only suitable if you intend to
customise the rendering for a single table (otherwise you'll end up having to
copy & paste the method to every table you want to modify – which violates
DRY).

For convenience, a bunch of commonly used/useful values are passed to
``render_FOO`` functions, when writing the signature, accept the arguments
you're interested in, and collect the rest in a ``**kwargs`` argument.

:param value: the value for the cell retrieved from the :term:`table data`
:param record: the entire record for the row from :term:`table data`
:param column: the :class:`.Column` object
:param bound_column: the :class:`.BoundColumn` object
:param bound_row: the :class:`.BoundRow` object
:param table: alias for ``self``

.. code-block:: python

    >>> import django_tables as tables
    >>> class SimpleTable(tables.Table):
    ...     row_number = tables.Column()
    ...     id = tables.Column()
    ...     age = tables.Column()
    ...
    ...     def render_row_number(self, **kwargs):
    ...         value = getattr(self, '_counter', 0)
    ...         self._counter = value + 1
    ...         return 'Row %d' % value
    ...
    ...     def render_id(self, value, **kwargs):
    ...         return '<%s>' % value
    ...
    >>> table = SimpleTable([{'age': 31, 'id': 10}, {'age': 34, 'id': 11}])
    >>> for cell in table.rows[0]:
    ...     print cell
    ...
    Row 0
    <10>
    31


.. _custom-template:

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

.. _template-tags.render_table:

render_table
------------

Renders a :class:`~django_tables.tables.Table` object to HTML and includes as
many features as possible.

Sample usage:

.. code-block:: django

    {% load django_tables %}
    {% render_table table %}

This tag temporarily modifies the :class:`.Table` object while it is being
rendered. It adds a ``request`` attribute to the table, which allows
:class:`Column` objects to have access to a ``RequestContext``. See
:class:`.TemplateColumn` for an example.


.. _template-tags.set_url_param:

set_url_param
-------------

This template tag is a utility that allows you to update a portion of the
query-string without overwriting the entire thing. However you shouldn't need
to use this template tag unless you are rendering the table from scratch (i.e.
not using ``as_html()`` or ``{% render_table %}``).

This is very useful if you want the give your users the ability to interact
with your table (e.g. change the ordering), because you will need to create
urls with the appropriate queries.

Let's assume we have the querystring ``?search=pirates&sort=name&page=5`` and
we want to update the ``sort`` parameter:

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

:class:`Accessor` Objects:
--------------------------

.. autoclass:: django_tables.utils.Accessor
    :members:


:class:`Table` Objects:
-----------------------

.. autoclass:: django_tables.tables.Table


:class:`Table.Meta` Objects:
----------------------------

.. class:: Table.Meta

    .. attribute:: attrs

        Allows custom HTML attributes to be specified which will be added to
        the ``<table>`` tag of any table rendered via
        :meth:`~django_tables.tables.Table.as_html` or the
        :ref:`template-tags.render_table` template tag.

        Default: ``{}``

        :type: :class:`dict`

    .. attribute:: sortable

        Does the table support ordering?

        Default: :const:`True`

        :type: :class:`bool`

    .. attribute:: order_by

        The default ordering. e.g. ``('name', '-age')``

        Default: ``()``

        :type: :class:`tuple`


:class:`TableData` Objects:
------------------------------

.. autoclass:: django_tables.tables.TableData
    :members: __init__, order_by, __getitem__, __len__


:class:`TableOptions` Objects:
------------------------------

.. autoclass:: django_tables.tables.TableOptions
    :members:


:class:`Column` Objects:
------------------------

.. autoclass:: django_tables.columns.Column


:class:`CheckBoxColumn` Objects:
--------------------------------

.. autoclass:: django_tables.columns.CheckBoxColumn
    :members:


:class:`LinkColumn` Objects:
----------------------------

.. autoclass:: django_tables.columns.LinkColumn
    :members:


:class:`TemplateColumn` Objects:
--------------------------------

.. autoclass:: django_tables.columns.TemplateColumn
    :members:


:class:`BoundColumns` Objects
-----------------------------

.. autoclass:: django_tables.columns.BoundColumns
    :members: all, items, names, sortable, visible, __iter__,
              __contains__, __len__, __getitem__


:class:`BoundColumn` Objects
----------------------------

.. autoclass:: django_tables.columns.BoundColumn
    :members:


:class:`BoundRows` Objects
--------------------------

.. autoclass:: django_tables.rows.BoundRows
    :members: all, page, __iter__, __len__, count


:class:`BoundRow` Objects
-------------------------

.. autoclass:: django_tables.rows.BoundRow
    :members: __getitem__, __contains__, __iter__, record, table


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
    :members: __unicode__, __contains__, __getitem__, cmp


Glossary
========

.. glossary::

    accessor
        Refers to an :class:`~django_tables.utils.Accessor` object

    bare orderby
        The non-prefixed form of an :class:`~django_tables.utils.OrderBy`
        object. Typically the bare form is just the ascending form.

        Example: ``age`` is the bare form of ``-age``

    column name
        The name given to a column. In the follow example, the *column name* is
        ``age``.

        .. code-block:: python

            class SimpleTable(tables.Table):
                age = tables.Column()

    table
        The traditional concept of a table. i.e. a grid of rows and columns
        containing data.

    view
        A Django view.

    record
        A single Python object used as the data for a single row.

    render
        The act of serialising a :class:`~django_tables.tables.Table` into
        HTML.

    template
        A Django template.

    table data
        An interable of :term:`records <record>` that
        :class:`~django_tables.tables.Table` uses to populate its rows.
