.. default-domain:: py

================================================
django-tables2 - An app for creating HTML tables
================================================

django-tables2 simplifies the task of turning sets of datainto HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
``django.forms`` does for HTML forms.

Quick start guide
=================

1. Download and install from https://github.com/bradleyayers/django-tables2.
   Grab a ``.tar.gz`` of the latest tag, and run ``pip install <tar.gz>``.
2. Hook the app into your Django project by adding ``'django_tables2'`` to your
   ``INSTALLED_APPS`` setting.
3. Write a subclass of :class:`~django_tables2.tables.Table` that describes the
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


The first step is to subclass :class:`~django_tables2.tables.Table` and describe
the table structure. This is done by creating a column for each attribute in
the :term:`table data`.

.. code-block:: python

    import django_tables2 as tables

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
:meth:`.Table.as_html` method:

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

This approach is easy, but it has a major problem in that it clobbers
(overwrites) any existing querystring values when pagination or
sorting are used. For these reasons you should use the :ref:`template tag
<template-tags.render_table>` instead:

.. code-block:: django

    {% load django_tables2 %}
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

    import django_tables2 as tables

    class CountryTable(tables.Table):
        name = tables.Column()
        population = tables.Column()
        tz = tables.Column(verbose_name='Time Zone')
        visits = tables.Column()

        class Meta:
            attrs = {'class': 'paleblue'}

The last thing to do is to include the stylesheet in the template.

.. code-block:: html

    <link rel="stylesheet" type="text/css" href="{{ STATIC_URL }}django_tables2/themes/paleblue/css/screen.css" />

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
be changed via the :attr:`~django_tables2.columns.Column.accessor` argument.

Any iterable can be used as table data, and there's builtin support for
:class:`QuerySet` objects (to ensure they're handled effeciently).


.. _ordering:

Ordering
========

.. note::

    If you want to change the order in which columns are displayed, see
    :attr:`Table.Meta.sequence`. Alternatively if you're interested in the
    order of records within the table, read on.

Changing the way records in a table are ordered is easy and can be controlled
via the :attr:`.Table.Meta.order_by` option. The following examples all achieve
the same thing:

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
hyperlinks that add the querystring field ``sort`` to the current URL. This
means your view will need to look something like:

.. code-block:: python

    def home(request):
        countries = Country.objects.all()
        table = CountryTable(countries, order_by=request.GET.get('sort'))
        return render_to_response('home.html', {'table': table},
                                  context_instance=RequestContext(request))

See :ref:`query-string-fields` for more details.

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

Where the table is :ref:`backed by a model <tables-for-models>`, the database
will handle the sorting. Where this is not the case, the Python ``cmp``
function is used and the following mechanism is used as a fallback when
comparing across different types:

.. code-block:: python

    def cmp_(x, y):
        try:
            return cmp(x, y)
        except TypeError:
            return cmp((repr(x.__class__), id(x.__class__), x),
                       (repr(y.__class__), id(y.__class__), y))


.. _column-headers:

Column headers
==============

The header cell for each column comes from the column's
:meth:`~django_tables2.columns.BoundColumn.header` method. By default this
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


.. _query-string-fields:

Querystring fields
==================

The table from ``{% render_table %}`` supports sortable columns, and
pagination. These options are passed via the querystring, and must be passed to
the table in order for them to have an effect, e.g.

.. code-block:: python

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        table.paginate(page=request.GET.get("page", 1))
        table.order_by = request.GET.get("sort")
        return render_to_response("people_listing.html", {"table": table},
                                  context_instance=RequestContext(request))

This works well unless you have more than one table on a page. In that
scenarios, all the tables will try to use the same ``sort`` and ``page``
querystring fields.

In following ``django.forms`` the solution, a prefix can be specified for each
table:

.. code-block:: python

    def people_listing(request):
        table1 = PeopleTable(Person.objects.all(), prefix="1-")  # prefix specified
        table1.paginate(page=request.GET.get("1-page", 1))
        table1.order_by = request.GET.get("1-sort")

        table2 = PeopleTable(Person.objects.all(), prefix="2-")  # prefix specified
        table2.paginate(page=request.GET.get("2-page", 1))
        table2.order_by = request.GET.get("2-sort")

        return render_to_response("people_listing.html",
                                  {"table1": table1, "table2": table2},
                                  context_instance=RequestContext(request))

Taking this one step further, rather than just specifying a prefix, it's
possible to specify the base name for each option. Suppose you don't like the
name ``sort`` for the ordering option -- you could change it to ``ob``
(initialism of *order by*). Such options are configured via the ``FOO_field``
properties:

- ``order_by_field``
- ``page_field``
- ``per_page_field`` -- **note:** this field currently isn't used by
  ``{% render_table %}``

Example:

.. code-block:: python

    def people_listing(request):
        table = PeopleTable(Person.objects.all(), order_by_field="ob",
                            page_field="p")
        table.paginate(page=request.GET.get("p", 1))
        table.order_by = request.GET.get("ob")
        return render_to_response("people_listing.html", {"table": table},
                                  context_instance=RequestContext(request))

In following django-tables2 conventions, these options can be configured in
different places:

- ``Meta`` class in the table definition.
- Table constructor.
- Table instance property.

For convenience there is a set of ``prefixed_FOO_field`` properties that exist
on each table instance and return the final querystring field names (i.e.
combines the prefix with the base name). This allows the above view to be
re-written:

.. code-block:: python

    def people_listing(request):
        table = PeopleTable(Person.objects.all(), order_by_field="ob",
                            page_field="p")
        table.paginate(page=request.GET.get(table.prefixed_page_field, 1))
        table.order_by = request.GET.get(table.prefixed_order_by_field)
        return render_to_response("people_listing.html", {"table": table},
                                  context_instance=RequestContext(request))


Config objects
==============

Config objects make it easier to configure a table. At the moment there's just
one -- ``RequestConfig``. It takes a ``HttpRequest`` and is able to configure a
table's sorting and pagination by extracting querystring data.

The view from the previous section can be rewritten without the boilerplate:

.. code-block:: python

    from django_tables2 import RequestConfig

    def people_listing(request):
        table = PeopleTable(Person.objects.all(), order_by_field="ob",
                            page_field="p")
        RequestConfig(request).configure(table)
        return render_to_response("people_listing.html", {"table": table},
                                  context_instance=RequestContext(request))

See :class:`.RequestConfig` for details.


.. _pagination:

Pagination
==========

Pagination is easy, just call :meth:`.Table.paginate` and
pass in the current page number, e.g.

.. code-block:: python

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        table.paginate(page=request.GET.get('page', 1))
        return render_to_response('people_listing.html', {'table': table},
                                  context_instance=RequestContext(request))

.. _custom-rendering:

Custom rendering
================

Various options are available for changing the way the table is :term:`rendered
<render>`. Each approach has a different balance of ease-of-use and
flexibility.

CSS
---

In order to use CSS to style a table, you'll probably want to add a
``class`` or ``id`` attribute to the ``<table>`` element. ``django-tables2`` has
a hook that allows abitrary attributes to be added to the ``<table>`` tag.

.. code-block:: python

    >>> import django_tables2 as tables
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

    >>> import django_tables2 as tables
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

    >>> import django_tables2 as tables
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


For complicated columns, it's sometimes necessary to return HTML from a
:meth:`~Column.render` method, but the string must be marked as safe (otherwise
it will be escaped when the table is rendered). This can be achieved by using
the :func:`mark_safe` function.

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
:class:`.Table` subclass into your own template, and render it yourself:

.. code-block:: django

    {% spaceless %}
    {% load django_tables2 %}
    {% if table.page %}
    <div class="table-container">
    {% endif %}
    <table{% if table.attrs %} {{ table.attrs.as_html }}{% endif %}>
        <thead>
            <tr class="{% cycle "odd" "even" %}">
            {% for column in table.columns %}
            {% if column.sortable %}
                {% with column.order_by as ob %}
                <th class="{% spaceless %}{% if column.sortable %}sortable {% endif %}{% if ob %}{% if ob.is_descending %}desc{% else %}asc{% endif %}{% endif %}{% endspaceless %}"><a href="{% if ob %}{% set_url_param sort=ob.opposite %}{% else %}{% set_url_param sort=column.name %}{% endif %}">{{ column.header }}</a></th>
                {% endwith %}
            {% else %}
                <th>{{ column.header }}</th>
            {% endif %}
            {% endfor %}
            </tr>
        </thead>
        <tbody>
            {% for row in table.page.object_list|default:table.rows %} {# support pagination #}
            <tr class="{% cycle "odd" "even" %}">
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
    {% if table.page %}
    <ul class="pagination">
        {% if table.page.has_previous %}
        <li class="previous"><a href="{% set_url_param page=table.page.previous_page_number %}">Previous</a></li>
        {% endif %}
        <li class="current">Page {{ table.page.number }} of {{ table.paginator.num_pages }}</li>
        {% if table.page.has_next %}
        <li class="next"><a href="{% set_url_param page=table.page.next_page_number %}">Next</a></li>
        {% endif %}
    </ul>
    </div>
    {% endif %}
    {% endspaceless %}

.. note::

    This is a complicated example, and is actually the template code that
    ``{% render_table %}`` uses.


.. _template_tags:

Template tags
=============

.. _template-tags.render_table:

render_table
------------

Renders a :class:`~django_tables2.tables.Table` object to HTML and enables as
many features in the output as possible.

.. code-block:: django

    {% load django_tables2 %}
    {% render_table table %}

    {# Alternatively a specific template can be used #}
    {% render_table table "path/to/custom_table_template.html" %}

If the second argument (template path) is given, the template will be rendered
with a ``RequestContext`` and the table will be in the variable ``table``.

.. note::

    This tag temporarily modifies the ``Table`` object while it is being
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


Class Based Generic Mixins
==========================

Django 1.3 introduced `class based views`__ as a mechanism to reduce the
repetition in view code. django-tables2 comes with a single class based view
mixin: ``SingleTableMixin``. It makes it trivial to incorporate a table into a
view/template, however it requires a few variables to be defined on the view:

- ``table_class`` –- the table class to use, e.g. ``SimpleTable``
- ``table_data`` (or ``get_table_data()``) -- the data used to populate the
  table
- ``context_table_name`` -- the name of template variable containing the table
  object

.. __: https://docs.djangoproject.com/en/1.3/topics/class-based-views/

For example:

.. code-block:: python

    from django_tables2.views import SingleTableMixin
    from django.generic.views.list import ListView


    class Simple(models.Model):
        first_name = models.CharField(max_length=200)
        last_name = models.CharField(max_length=200)


    class SimpleTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()


    class MyTableView(SingleTableMixin, ListView):
        model = Simple
        table_class = SimpleTable


The template could then be as simple as:

.. code-block:: django

    {% load django_tables2 %}
    {% render_table table %}

Such little code is possible due to the example above taking advantage of
default values and ``SimpleTableMixin``'s eagarness at finding data sources
when one isn't explicitly defined.

.. note::

    If you want more than one table on a page, at the moment the simplest way
    to do it is to use ``SimpleTableMixin`` for one table, and write the
    boilerplate for the other yourself in ``get_context_data()``. Obviously
    this isn't particularly elegant, and as such will hopefully be resolved in
    the future.


Table Mixins
============

It's possible to create a mixin for a table that overrides something, however
unless it itself is a subclass of :class:`.Table` class
variable instances of :class:`.Column` will **not** be added to the class which is using the mixin.

Example::

    >>> class UselessMixin(object):
    ...     extra = tables.Column()
    ...
    >>> class TestTable(UselessMixin, tables.Table):
    ...     name = tables.Column()
    ...
    >>> TestTable.base_columns.keys()
    ['name']

To have a mixin contribute a column, it needs to be a subclass of
:class:`~django_tables2.tables.Table`. With this in mind the previous example
*should* have been written as follows::

    >>> class UsefulMixin(tables.Table):
    ...     extra = tables.Column()
    ...
    >>> class TestTable(UsefulMixin, tables.Table):
    ...     name = tables.Column()
    ...
    >>> TestTable.base_columns.keys()
    ['extra', 'name']


.. _tables-for-models:

Tables for models
=================

Most of the time you'll probably be making tables to display queryset data, and
writing such tables involves a lot of duplicate code, e.g.::

    >>> class Person(models.Model):
    ...     first_name = models.CharField(max_length=200)
    ...     last_name = models.CharField(max_length=200)
    ...     user = models.ForeignKey("auth.User")
    ...     dob = models.DateField()
    ...
    >>> class PersonTable(tables.Table):
    ...     first_name = tables.Column()
    ...     last_name = tables.Column()
    ...     user = tables.Column()
    ...     dob = tables.Column()
    ...

Often a table will become quite complex after time, e.g. `table.render_foo`_,
changing ``verbose_name`` on columns, or adding an extra
:class:`~.CheckBoxColumn`.

``django-tables2`` offers the :attr:`.Table.Meta.model` option to ease the pain.
The ``model`` option causes the table automatically generate columns for the
fields in the model. This means that the above table could be re-written as
follows::

    >>> class PersonTable(tables.Table):
    ...     class Meta:
    ...         model = Person
    ...
    >>> PersonTable.base_columns.keys()
    ['first_name', 'last_name', 'user', 'dob']

If you want to customise one of the columns, simply define it the way you would
normally::

    >>> from django_tables2 import A
    >>> class PersonTable(tables.Table):
    ...     user = tables.LinkColumn("admin:auth_user_change", args=[A("user.pk")])
    ...
    ...     class Meta:
    ...         model = Person
    ...
    >>> PersonTable.base_columns.keys()
    ['first_name', 'last_name', 'dob', 'user']

It's not immediately obvious but if you look carefully you'll notice that the
order of the fields has now changed -- ``user`` is now last, rather than
``dob``. This follows the same behaviour of Django's model forms, and can be
fixed in a similar way -- the :attr:`.Table.Meta.sequence` option::

    >>> class PersonTable(tables.Table):
    ...     user = tables.LinkColumn("admin:auth_user_change", args=[A("user.pk")])
    ...
    ...     class Meta:
    ...         model = Person
    ...         sequence = ("first_name", "last_name", "user", "dob")
    ...
    >>> PersonTable.base_columns.keys()
    ['first_name', 'last_name', 'user', 'dob']

… or use a shorter approach that makes use of the special ``"..."`` item::

    >>> class PersonTable(tables.Table):
    ...     user = tables.LinkColumn("admin:auth_user_change", args=[A("user.pk")])
    ...
    ...     class Meta:
    ...         model = Person
    ...         sequence = ("...", "dob")
    ...
    >>> PersonTable.base_columns.keys()
    ['first_name', 'last_name', 'user', 'dob']


API Reference
=============

:class:`Accessor` Objects:
--------------------------

.. autoclass:: django_tables2.utils.Accessor


:class:`RequestConfig` Objects:
-------------------------------

.. autoclass:: django_tables2.config.RequestConfig


:class:`Table` Objects:
-----------------------

.. autoclass:: django_tables2.tables.Table
    :members:


:class:`Table.Meta` Objects:
----------------------------

.. class:: Table.Meta

    Provides a way to define *global* settings for table, as opposed to
    defining them for each instance.

    .. attribute:: attrs

        Allows custom HTML attributes to be specified which will be added to
        the ``<table>`` tag of any table rendered via
        :meth:`.Table.as_html` or the
        :ref:`template-tags.render_table` template tag.

        :type: ``dict``
        :default: ``{}``

        This is typically used to enable a theme for a table (which is done by
        adding a CSS class to the ``<table>`` element). i.e.::

            class SimpleTable(tables.Table):
                name = tables.Column()

                class Meta:
                    attrs = {"class": "paleblue"}

        .. note::

            This functionality is also available via the ``attrs`` keyword
            argument to a table's constructor.

    .. attribute:: empty_text

        Defines the text to display when the table has no rows.

        :type: ``string``
        :default: ``None``

        If the table is empty and ``bool(empty_text)`` is ``True``, a row is
        displayed containing ``empty_text``. This is allows a message such as
        *There are currently no FOO.* to be displayed.

        .. note::

            This functionality is also available via the ``empty_text`` keyword
            argument to a table's constructor.

    .. attribute:: exclude

        Defines which columns should be excluded from the table. This is useful
        in subclasses to exclude columns in a parent.

        :type: tuple of ``string`` objects
        :default: ``()``

        Example::

            >>> class Person(tables.Table):
            ...     first_name = tables.Column()
            ...     last_name = tables.Column()
            ...
            >>> Person.base_columns
            {'first_name': <django_tables2.columns.Column object at 0x10046df10>,
            'last_name': <django_tables2.columns.Column object at 0x10046d8d0>}
            >>> class ForgetfulPerson(Person):
            ...     class Meta:
            ...         exclude = ("last_name", )
            ...
            >>> ForgetfulPerson.base_columns
            {'first_name': <django_tables2.columns.Column object at 0x10046df10>}

        .. note::

            This functionality is also available via the ``exclude`` keyword
            argument to a table's constructor.

            However, unlike some of the other ``Meta`` options, providing the
            ``exclude`` keyword to a table's constructor **won't override** the
            ``Meta.exclude``. Instead, it will be effectively be *added*
            to it. i.e. you can't use the constructor's ``exclude`` argument to
            *undo* an exclusion.

    .. attribute:: model

        A model to inspect and automatically create corresponding columns.

        :type: Django model
        :default: ``None``

        This option allows a Django model to be specified to cause the table to
        automatically generate columns that correspond to the fields in a
        model.

    .. attribute:: order_by

        The default ordering. e.g. ``('name', '-age')``. A hyphen ``-`` can be
        used to prefix a column name to indicate *descending* order.

        :type: ``tuple``
        :default: ``()``

        .. note::

            This functionality is also available via the ``order_by`` keyword
            argument to a table's constructor.

    .. attribute:: sequence

        The sequence of the table columns. This allows the default order of
        columns (the order they were defined in the Table) to be overridden.

        :type: any iterable (e.g. ``tuple`` or ``list``)
        :default: ``()``

        The special item ``"..."`` can be used as a placeholder that will be
        replaced with all the columns that weren't explicitly listed. This
        allows you to add columns to the front or back when using inheritence.

        Example::

            >>> class Person(tables.Table):
            ...     first_name = tables.Column()
            ...     last_name = tables.Column()
            ...
            ...     class Meta:
            ...         sequence = ("last_name", "...")
            ...
            >>> Person.base_columns.keys()
            ['last_name', 'first_name']

        The ``"..."`` item can be used at most once in the sequence value. If
        it's not used, every column *must* be explicitly included. e.g. in the
        above example, ``sequence = ("last_name", )`` would be **invalid**
        because neither ``"..."`` or ``"first_name"`` were included.

        .. note::

            This functionality is also available via the ``sequence`` keyword
            argument to a table's constructor.

    .. attribute:: sortable

        Whether columns are by default sortable, or not. i.e. the fallback for
        value for a column's sortable value.

        :type: ``bool``
        :default: ``True``

        If the ``Table`` and ``Column`` don't specify a value, a column's
        ``sortable`` value will fallback to this. object specify. This provides
        an easy mechanism to disable sorting on an entire table, without adding
        ``sortable=False`` to each ``Column`` in a ``Table``.

        .. note::

            This functionality is also available via the ``sortable`` keyword
            argument to a table's constructor.

    .. attribute:: template

        The default template to use when rendering the table.

        :type: ``unicode``
        :default: ``django_tables2/table.html``

        .. note::

            This functionality is also available via the ``template`` keyword
            argument to a table's constructor.


:class:`TableData` Objects:
------------------------------

.. autoclass:: django_tables2.tables.TableData
    :members: __init__, order_by, __getitem__, __len__


:class:`Column` Objects:
------------------------

.. autoclass:: django_tables2.columns.Column


:class:`CheckBoxColumn` Objects:
--------------------------------

.. autoclass:: django_tables2.columns.CheckBoxColumn
    :members:


:class:`LinkColumn` Objects:
----------------------------

.. autoclass:: django_tables2.columns.LinkColumn
    :members:


:class:`TemplateColumn` Objects:
--------------------------------

.. autoclass:: django_tables2.columns.TemplateColumn
    :members:


:class:`BoundColumns` Objects
-----------------------------

.. autoclass:: django_tables2.columns.BoundColumns
    :members: all, items, sortable, visible, __iter__,
              __contains__, __len__, __getitem__


:class:`BoundColumn` Objects
----------------------------

.. autoclass:: django_tables2.columns.BoundColumn
    :members:


:class:`BoundRows` Objects
--------------------------

.. autoclass:: django_tables2.rows.BoundRows
    :members: __iter__, __len__, count


:class:`BoundRow` Objects
-------------------------

.. autoclass:: django_tables2.rows.BoundRow
    :members: __getitem__, __contains__, __iter__, record, table


:class:`AttributeDict` Objects
------------------------------

.. autoclass:: django_tables2.utils.AttributeDict
    :members:


:class:`OrderBy` Objects
------------------------

.. autoclass:: django_tables2.utils.OrderBy
    :members:


:class:`OrderByTuple` Objects
-----------------------------

.. autoclass:: django_tables2.utils.OrderByTuple
    :members: __unicode__, __contains__, __getitem__, cmp


Glossary
========

.. glossary::

    accessor
        Refers to an :class:`~django_tables2.utils.Accessor` object

    bare orderby
        The non-prefixed form of an :class:`~django_tables2.utils.OrderBy`
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
        The act of serialising a :class:`~django_tables2.tables.Table` into
        HTML.

    template
        A Django template.

    table data
        An interable of :term:`records <record>` that
        :class:`~django_tables2.tables.Table` uses to populate its rows.


Upgrading from django-tables Version 1
======================================

- Change your ``INSTALLLED_APPS`` entry from ``django_tables.app`` to
  ``django_tables2``.

- Change all your import references from ``django_tables`` to
  ``django_tables2``.

- Replace all references to the old ``MemoryTable`` and ``ModelTable``
  classes with simply ``Table``.

- In your templates, load the ``django_tables2`` template library;
  ``{% load django_tables2 %}`` instead of ``{% load tables %}``.

- A table object is no longer iterable; rather than ``for row in table``,
  instead you now do explicitly: ``for row in table.rows``.

- If you were using ``row.data`` to access a row's underlying data,
  replace it with ``row.record`` instead.

- When declaring columns, replace the use of::

    name_in_dataset = tables.Column(name="wanted_column_name")

  with::

    wanted_column_name = tables.Column(accessor="name_in_dataset")

- When declaring columns, replace the use of::

     column_to_override = tables.Column(name="wanted_column_name", data="name_in_dataset")

  with::

     wanted_column_name = tables.Column(accessor="name_in_dataset")

  and exclude ``column_to_override`` via the table meta data.

- When rendering columns, change ``{{ column }}`` to ``{{ column.header }}``.

- When generating the link to sort the column, instead of:

  .. code-block:: django

     {% set_url_param sort=column.name_toggled %}

  use:

  .. code-block:: django

       {% if column.order_by %}
            {% set_url_param sort=column.order_by.opposite %}
       {% else %}
            {% set_url_param sort=column.name %}
       {% endif %}

  You might want to use ``{% spaceless %}`` to make it more readable.

- Replace:

  .. code-block:: django

      {{ column.is_ordered_reverse }} and {{ column.is_ordered_straight }}

  with:

  .. code-block:: django

      {{ column.order_by.is_descending }} and {{ column.order_by.is_ascending }}
