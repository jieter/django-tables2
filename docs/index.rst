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
        {'name': 'Germany', 'population': 81, 'tz': 'UTC +1', 'visits': 2},
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
                                  context_instance=RequestContext(request))

In your template, the easiest way to :term:`render` the table is via the
:meth:`~django_tables.tables.Table.as_html` method:

.. code-block:: django

    {{ table.as_html }}

…which will render something like:

+--------------+------------+-----------+--------+
| Country Name | Population | Time Zone | Visit  |
+==============+============+===========+========+
| Australia    | 21         | UTC +10   | 1      |
+--------------+------------+-----------+--------+
| Germany      | 81         | UTC +1    | 2      |
+--------------+------------+-----------+--------+
| Mexico       | 107        | UTC -6    | 0      |
+--------------+------------+-----------+--------+

This approach is easy, but it's not fully featured (e.g. no pagination, no
sorting). Don't worry it's very easy to add these. First, you must render the
table via the :ref:`template tag <template-tags.render_table>` rather than
``as_html()``:

.. code-block:: django

    {% load django_tables %}
    {% render_table table %}

.. note::

    ``{% render_table %}`` requires that the ``TEMPLATE_CONTEXT_PROCESSORS``
    setting contains ``"django.core.context_processors.request"``. See
    :ref:`template-tags.render_table` for details.

This is all that's required for the template, but in the view you'll need to
tell the table to which column to order by, and which page of data to display
(pagination). This is achieved as follows:

.. code-block:: python

    def home(request):
        countries = Country.objects.all()
        table = CountryTable(countries, order_by=request.GET.get('sort'))
        table.paginate(page=request.GET.get('page', 1))
        return render_to_response('home.html', {'table': table},
                                  context_instance=RequestContext(request))

See :ref:`ordering`, and :ref:`pagination` for more information.

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

Changing the way a table is ordered is easy and can be controlled via the
:attr:`.Table.Meta.order_by` option. The following examples all achieve the
same thing:

.. code-block:: python

    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            order_by = 'name'

By passing in a value for ``order_by`` into the ``Table`` constructor, the
``Meta.order_by`` option can be overridden on a per-instance basis.

.. code-block:: python

    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable(..., order_by='name')

This approach allows column sorting to be enabled for use with the ``{%
render_table %}`` template tag. The template tag converts column headers into
hyperlinks that add the querystring parameter ``sort`` to the current URL. This
means your view will need to look something like:

.. code-block:: python

    def home(request):
        countries = Country.objects.all()
        table = CountryTable(countries, order_by=request.GET.get('sort'))
        return render_to_response('home.html', {'table': table},
                                  context_instance=RequestContext(request))

The final approach allows both of the previous approaches to be overridden. The
instance property ``order_by`` can be

.. code-block:: python

    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable(...)
    table.order_by = 'name'

----

By default all table columns support sorting. This means that if you're using
the :ref:`template tag <template-tags.render_table>` to render the table,
users can sort the table based on any column by clicking the corresponding
header link.

In some cases this may not be appropriate. For example you may have a column
which displays data that isn't in the dataset:

.. code-block:: python

    class SimpleTable(tables.Table):
        name = tables.Column()
        lucky_rating = tables.Column()

        class Meta:
            sortable = False

        def render_lucky_rating(self):
            import random
            return random.randint(1, 10)

In these types of scenarios, it's simply not possible to sort the table based
on column data that isn't in the dataset. The solution is to disable sorting
for these columns.

Sorting can be disabled on a column, table, or table instance basis via the
:attr:`.Table.Meta.sortable` option.

To disable sorting by default for all columns:

.. code-block:: python

    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            sortable = False

To disable sorting for a specific table instance:

.. code-block:: python

    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable(..., sortable=False)
    # or
    table.sortable = False


.. _column-headers:

Column headers
==============

The header cell for each column comes from the column's
:meth:`~django_tables.columns.BoundColumn.header` method. By default this
method returns the column's ``verbose_name``, which is either explicitly
specified, or generated automatically based on the column name.

When using queryset input data, rather than falling back to the column name if
a ``verbose_name`` has not been specified explicitly, the queryset model's
field ``verbose_name`` is used.

Consider the following:

    >>> class Person(models.Model):
    ...     first_name = models.CharField(verbose_name='FIRST name', max_length=200)
    ...     last_name = models.CharField(max_length=200)
    ...     region = models.ForeignKey('Region')
    ...
    >>> class Region(models.Model):
    ...     name = models.CharField(max_length=200)
    ...
    >>> class PersonTable(tables.Table):
    ...     first_name = tables.Column()
    ...     ln = tables.Column(accessor='last_name')
    ...     region_name = tables.Column(accessor='region.name')
    ...
    >>> table = PersonTable(Person.objects.all())
    >>> table.columns['first_name'].verbose_name
    u'FIRST name'
    >>> table.columns['ln'].verbose_name
    u'Last name'
    >>> table.columns['region_name'].verbose_name
    u'Name'

As you can see in the last example, the results are not always desirable when
an accessor is used to cross relationships. To get around this be careful to
define a ``verbose_name`` on such columns.


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
``render_FOO`` functions, when writing the signature, simply accept the
arguments you're interested in, and the function will recieve them

.. note:: Due to the implementation, a "catch-extra" arguments (e.g. ``*args``
    or ``**kwargs``) will not recieve any arguments. This is because
    ``inspect.getargsspec()`` is used to check what arguments a ``render_FOO``
    method expect, and only to supply those.

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
    ...     def render_row_number(self):
    ...         value = getattr(self, '_counter', 0)
    ...         self._counter = value + 1
    ...         return 'Row %d' % value
    ...
    ...     def render_id(self, value):
    ...         return '<%s>' % value
    ...
    >>> table = SimpleTable([{'age': 31, 'id': 10}, {'age': 34, 'id': 11}])
    >>> for cell in table.rows[0]:
    ...     print cell
    ...
    Row 0
    <10>
    31


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
    ...     def render(self, value):
    ...         return value.upper()
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

See :ref:`table.render_foo` for a list of arguments that can be accepted.

Which, when displayed in a browser, would look something like this:

+-----------------------+--------------------------+
| Normal                | Angry                    |
+=======================+==========================+
| May I have some food? | GIVE ME THE FOOD NOW!    |
+-----------------------+--------------------------+
| Hello!                | WHAT ARE YOU LOOKING AT? |
+-----------------------+--------------------------+


For complicated columns, it's sometimes necessary to return HTML from a :meth:`~Column.render` method, but the string
must be marked as safe (otherwise it will be escaped when the table is
rendered). This can be achieved by using the :func:`mark_safe` function.

.. code-block:: python

    >>> from django.utils.safestring import mark_safe
    >>>
    >>> class ImageColumn(tables.Column):
    ...     def render(self, value):
    ...         return mark_safe('<img src="/media/img/%s.jpg" />' % value)
    ...


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
            {% empty %}
                {% if table.empty_text %}
                <tr><td colspan="{{ table.columns|length }}">{{ table.empty_text }}</td></tr>
                {% endif %}
            {% endfor %}
        </tbody>
    </table>


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

This tag requires that the template in which it's rendered contains the
``HttpRequest`` inside a ``request`` variable. This can be achieved by ensuring
the ``TEMPLATE_CONTEXT_PROCESSORS`` setting contains
``"django.core.context_processors.request"``. By default it is not included,
and the setting itself is not even defined within your project's
``settings.py``. To resolve this simply add the following to your
``settings.py``:

.. code-block:: python

    TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        "django.core.context_processors.static",
        "django.contrib.messages.context_processors.messages",
        "django.core.context_processors.request",
    )


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

    Provides a way to define *global* settings for table, as opposed to
    defining them for each instance.

    .. attribute:: attrs

        Allows custom HTML attributes to be specified which will be added to
        the ``<table>`` tag of any table rendered via
        :meth:`~django_tables.tables.Table.as_html` or the
        :ref:`template-tags.render_table` template tag.

        This is typically used to enable a theme for a table (which is done by
        adding a CSS class to the ``<table>`` element). i.e.::

            class SimpleTable(tables.Table):
                name = tables.Column()

                class Meta:
                    attrs = {"class": "paleblue"}

        :type: ``dict``

        Default: ``{}``

    .. attribute:: empty_text

        Defines the text to display when the table has no rows.

    .. attribute:: exclude

        Defines which columns should be excluded from the table. This is useful
        in subclasses to exclude columns in a parent. e.g.

            >>> class Person(tables.Table):
            ...     first_name = tables.Column()
            ...     last_name = tables.Column()
            ...
            >>> Person.base_columns
            {'first_name': <django_tables.columns.Column object at 0x10046df10>,
            'last_name': <django_tables.columns.Column object at 0x10046d8d0>}
            >>> class ForgetfulPerson(Person):
            ...     class Meta:
            ...         exclude = ("last_name", )
            ...
            >>> ForgetfulPerson.base_columns
            {'first_name': <django_tables.columns.Column object at 0x10046df10>}

        :type: tuple of ``string`` objects

        Default: ``()``

    .. attribute:: order_by

        The default ordering. e.g. ``('name', '-age')``. A hyphen ``-`` can be
        used to prefix a column name to indicate *descending* order.

        :type: :class:`tuple`

        Default: ``()``

    .. attribute:: sortable

        The default value for determining if a :class:`.Column` is sortable.

        If the ``Table`` and ``Column`` don't specify a value, a column's
        ``sortable`` value will fallback to this. object specify. This provides
        an easy mechanism to disable sorting on an entire table, without adding
        ``sortable=False`` to each ``Column`` in a ``Table``.

        :type: :class:`bool`

        Default: :const:`True`


:class:`TableData` Objects:
------------------------------

.. autoclass:: django_tables.tables.TableData
    :members: __init__, order_by, __getitem__, __len__


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
    :members: all, items, sortable, visible, __iter__,
              __contains__, __len__, __getitem__


:class:`BoundColumn` Objects
----------------------------

.. autoclass:: django_tables.columns.BoundColumn
    :members:


:class:`BoundRows` Objects
--------------------------

.. autoclass:: django_tables.rows.BoundRows
    :members: __iter__, __len__, count


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
