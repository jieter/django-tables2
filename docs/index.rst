.. default-domain:: py

================================================
django-tables2 - An app for creating HTML tables
================================================

django-tables2 simplifies transforming data into HTML tables. It does for HTML
tables what ``django.forms`` does for HTML forms. Features:

- Pagination
- Column sorting
- Built-in columns for common use-cases
- Easily extendable via subclassing
- Extendable template
- Generic view
- QuerySet support
- Built-in Django admin style theme (but can be easily remove).
- *ModelTable* support (think *django.forms.ModelForm*)


Tutorial
========

Install the app via ``pip install django-tables2``, then add
``'django_tables2'`` to ``INSTALLED_APPS``.

Find some data that you'd like to render as a table. A QuerySet will work, but
ease of demonstration we'll use a list of dicts:

.. code-block:: python

    countries = [
        {'name': 'Australia', 'population': 21, 'tz': 'UTC +10', 'visits': 1},
        {'name': 'Germany', 'population': 81, 'tz': 'UTC +1', 'visits': 2},
        {'name': 'Mexico', 'population': 107, 'tz': 'UTC -6', 'visits': 0},
    ]


First step is it write a Table class to describe the structure:

.. code-block:: python

    import django_tables2 as tables

    class CountryTable(tables.Table):
        name = tables.Column()
        population = tables.Column()
        tz = tables.Column(verbose_name='Time Zone')
        visits = tables.Column()

Now instantiate the table and pass in the data, then pass it to a template:

.. code-block:: python

    def home(request):
        table = CountryTable(countries)
        return render_to_response('home.html', {'table': table},
                                  context_instance=RequestContext(request))

Render the table in the template using the built-in template tag.

.. code-block:: django

    {% load render_table from django_tables2 %}
    {% render_table table %}

…which will give you somethinglike:

+--------------+------------+-----------+--------+
| Country Name | Population | Time Zone | Visit  |
+==============+============+===========+========+
| Australia    | 21         | UTC +10   | 1      |
+--------------+------------+-----------+--------+
| Germany      | 81         | UTC +1    | 2      |
+--------------+------------+-----------+--------+
| Mexico       | 107        | UTC -6    | 0      |
+--------------+------------+-----------+--------+

.. note::

    ``{% render_table %}`` requires that the ``TEMPLATE_CONTEXT_PROCESSORS``
    setting contains ``"django.core.context_processors.request"``. See
    :ref:`template-tags.render_table` for details.

To enable sorting and pagination, use a ``RequestConfig`` object in the view:

.. code-block:: python

    from django_tables2 import RequestConfig

    def home(request):
        table = CountryTable(countries)
        RequestConfig(request).configure(table)
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
    ordering of records within the table, read on.

Changing the way records in a table are ordered is easy and can be controlled
via the ``order_by`` option. This can be configured in three places:

1. ``Table.Meta.order_by``
2. ``Table(..., order_by=...)``
3. ``Table(...).order_by = ...``

Each of the above options takes prescendent over the previous.

The value must be either a comma separated string of column names, or a list of
column names. Generally you'll only use a single column name, but multiple are
supported to allow for multi-fallback-column ordering.

Ordering preference is passed via the querystring in a variable. The name of
the variable is determined by ``order_by_field`` (default: ``sort``). This can
be configured in three places:

1. ``Table.Meta.order_by_field``
2. ``Table(..., order_by_field=...)``
3. ``Table(...).order_by_field = ...``

``RequestConfig`` honors these values and *does the right thing*.

----

By default all table columns support ordering. This means that all the column
headers are rendered as links which allow the user to adjust the ordering of
the table data.

Ordering can be disabled on a table or column basis.

- ``Table.Meta.sortable = False`` -- default to disable ordering on columns
- ``Column(sortable=False)`` -- disable ordering for specific column

e.g. disable columns on all but one:

.. code-block:: python

    class SimpleTable(tables.Table):
        name = tables.Column()
        rating = tables.Column(sortable=True)

        class Meta:
            sortable = False

.. note::

    It's very unfortunate that the option is called ``sortable`` as opposed to
    ``orderable``. Expect this to change in the future.

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
method returns a titlised version of the column's ``verbose_name``.

When using queryset input data and a verbose name hasn't been explicitly
defined for a column, the corresponding model field's verbose name will be
used.

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
    >>> table.columns['first_name'].header
    u'FIRST Name'
    >>> table.columns['ln'].header
    u'Last name'
    >>> table.columns['region_name'].header
    u'Name'

As you can see in the last example, the results are not always desirable when
an accessor is used to cross relationships. To get around this be careful to
define a ``verbose_name`` on such columns.


.. _pagination:

Pagination
==========

Pagination is easy, just call :meth:`.Table.paginate` and
pass in the current page number, e.g.

.. code-block:: python

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        table.paginate(page=request.GET.get('page', 1), per_page=25)
        return render_to_response('people_listing.html', {'table': table},
                                  context_instance=RequestContext(request))

If you're using ``RequestConfig``, pass pagination options to ``configure()``,
e.g.:

.. code-block:: python

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        RequestConfig(request).configure(table, paginate={"per_page": 25})
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


.. _query-string-fields:

Querystring fields
==================

Tables pass data via the querystring to indicate sorting and pagination
preferences.

The names of the querystring variables are configurable via the options:

- ``order_by_field`` -- default: ``sort``
- ``page_field`` -- default: ``page``
- ``per_page_field`` -- default: ``per_page``, **note:** this field currently
  isn't used by ``{% render_table %}``

Each of these can be specified in three places:

- ``Table.Meta.foo``
- ``Table(..., foo=...)``
- ``Table(...).foo = ...``

If you're using multiple tables on a single page, you'll want to prefix these
fields with a table-specific name. e.g.

.. code-block:: python

    def people_listing(request):
        config = RequestConfig(request)
        table1 = PeopleTable(Person.objects.all(), prefix="1-")  # prefix specified
        table2 = PeopleTable(Person.objects.all(), prefix="2-")  # prefix specified
        config.configure(table1)
        config.configure(table2)
        return render_to_response("people_listing.html",
                                  {"table1": table1, "table2": table2},
                                  context_instance=RequestContext(request))

.. _column-attributes:

Column attributes
=================

Column attributes can be specified using the :class:`.Attrs` object. An
``Attrs`` object defines HTML tag attributes for one of more elements within
the column. Depending on the column, different elements are supported, however
``th`` and ``td`` are supported universally.

e.g.

.. code-block:: python

    >>> from django_tables2 import Attrs
    >>> import django_tables2 as tables
    >>>
    >>> class SimpleTable(tables.Table):
    ...     name = tables.Column(attrs=Attrs(th={"id": "foo"}))
    ...
    >>> SimpleTable(data).as_html()
    "{snip}<thead><tr><th id="foo" class="name">{snip}<tbody><tr><td class="name">{snip}"


``th`` and ``td`` are special cases because they're extended during rendering
to add the column name as a class. This is done to make writing CSS easier.
Have a look at each column's API reference to find which elements are
supported.


.. _builtin-columns:

Built-in columns
================

For common use-cases the following columns are included:

- :class:`.Column` -- generic column
- :class:`.CheckBoxColumn` -- renders checkbox form inputs
- :class:`.LinkColumn` -- renders ``<a href="...">`` tags
- :class:`.TemplateColumn` -- renders template code


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
:class:`.Table` subclass into your own template, and render it yourself.

Have a look at ``django_tables2/templates/django_tables2/table.html`` for an
example.

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


.. _template-tags.querystring:

querystring
-----------

A utility that allows you to update a portion of the query-string without
overwriting the entire thing.

Let's assume we have the querystring ``?search=pirates&sort=name&page=5`` and
we want to update the ``sort`` parameter:

.. code-block:: django

    {% querystring "sort"="dob" %}           # ?search=pirates&sort=dob&page=5
    {% querystring "sort"="" %}              # ?search=pirates&page=5
    {% querystring "sort"="" "search"="" %}  # ?page=5

    {% with "search" as key %}               # supports variables as keys
    {% querystring key="robots" %}           # ?search=robots&page=5
    {% endwith %}


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

    {% load render_table from django_tables2 %}
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


:class:`Attrs` Objects:
--------------------------

.. autoclass:: django_tables2.utils.Attrs


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
    :members: __getitem__, __contains__, __iter__, record, table, items


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
            {% querystring table.order_by_field=column.order_by.opposite %}
       {% else %}
            {% querystring table.order_by_field=column.name %}
       {% endif %}

  You might want to use ``{% spaceless %}`` to make it more readable.

- Replace:

  .. code-block:: django

      {{ column.is_ordered_reverse }} and {{ column.is_ordered_straight }}

  with:

  .. code-block:: django

      {{ column.order_by.is_descending }} and {{ column.order_by.is_ascending }}
