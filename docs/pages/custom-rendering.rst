Customizing table style
=======================

.. _css:

CSS
---

In order to use CSS to style a table, you'll probably want to add a
``class`` or ``id`` attribute to the ``<table>`` element. django-tables2 has
a hook that allows arbitrary attributes to be added to the ``<table>`` tag.

.. sourcecode:: python

    >>> import django_tables2 as tables
    >>>
    >>> class SimpleTable(tables.Table):
    ...     id = tables.Column()
    ...     age = tables.Column()
    ...
    ...     class Meta:
    ...         attrs = {"class": "mytable"}
    ...
    >>> table = SimpleTable()
    >>> # renders to something like this:
    '<table class="mytable">...'

By default, django-tables2 looks for the ``DJANGO_TABLES2_TABLE_ATTRS``
setting which allows you to define attributes globally for all tables.
For example, to have a Bootstrap5 table with hoverable rows 
and a light table header define it as follows:

.. sourcecode:: python

    DJANGO_TABLES2_TABLE_ATTRS = {
        'class': 'table table-hover',
        'thead': {
            'class': 'table-light',
        },
    }

You can also specify ``attrs`` attribute when creating a column. ``attrs``
is a dictionary which contains attributes which by default get rendered
on various tags involved with rendering a column. You can read more about
them in :ref:`column-attributes`. django-tables2 supports three different
dictionaries, this way you can give different attributes
to column tags in table header (``th``), rows (``td``) or footer (``tf``).

.. sourcecode:: python

    >>> import django_tables2 as tables
    >>>
    >>> class SimpleTable(tables.Table):
    ...     id = tables.Column(attrs={"td": {"class": "my-class"}})
    ...     age = tables.Column(attrs={"tf": {"bgcolor": "red"}})
    ...
    >>> table = SimpleTable()
    >>> # renders to something like this:
    '<tbody><tr><td class="my-class">...</td></tr>'
    >>> # and the footer will look like this:
    '<tfoot><tr> ... <td class="age" bgcolor="red"></tr></tfoot>''


.. _available-templates:

Available templates
-------------------

We ship a couple of different templates:

======================================== ======================================================
Template name                            Description
======================================== ======================================================
django_tables2/table.html                Basic table template (default).
django_tables2/bootstrap.html            Template using bootstrap 3 structure/classes
django_tables2/bootstrap4.html           Template using bootstrap 4 structure/classes
django_tables2/bootstrap-responsive.html Same as bootstrap, but wrapped in ``.table-responsive``
django_tables2/semantic.html             Template using semantic UI
======================================== ======================================================

By default, django-tables2 looks for the ``DJANGO_TABLES2_TEMPLATE`` setting
which is ``django_tables2/table.html`` by default.

If you use bootstrap 3 for your site, it makes sense to set the default to
the bootstrap 3 template::

    DJANGO_TABLES2_TEMPLATE = "django_tables2/bootstrap.html"

If you want to specify a custom template for selected tables in your project,
you can set a ``template_name`` attribute to your custom ``Table.Meta`` class::

    class PersonTable(tables.Table):

        class Meta:
            model = Person
            template_name = "django_tables2/semantic.html"

You can also use the ``template_name`` argument to the ``Table`` constructor to
override the template for a certain instance::

    table = PersonTable(data, template_name="django_tables2/bootstrap-responsive.html")

For none of the templates any CSS file is added to the HTML. You are responsible for
including the relevant style sheets for a template.

.. _custom-template:

Custom Template
---------------

And of course if you want full control over the way the table is rendered,
ignore the built-in generation tools, and instead pass an instance of your
`.Table` subclass into your own template, and render it yourself.

You should use one of the provided templates as a basis.
