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
    ...         attrs = {'class': 'mytable'}
    ...
    >>> table = SimpleTable()
    >>> # renders to something like this:
    '<table class="mytable">...'

.. _custom-template:

Custom Template
---------------

And of course if you want full control over the way the table is rendered,
ignore the built-in generation tools, and instead pass an instance of your
`.Table` subclass into your own template, and render it yourself.

Have a look at the ``django_tables2/table.html`` template for an example.

You can set `DJANGO_TABLES2_TEMPLATE` in your django settings to change the
default template django-tables2 looks for.
