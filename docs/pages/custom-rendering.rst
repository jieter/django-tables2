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

How about styling individual columns then? django-tables2 has you covered.
Ever single column gets a class attribute, which by default is the same
as the column's label. So every row of the ``SimpleTable()`` from previous
example will look like:

.. sourcecode:: html

    <tr>
      <td class="id">...</td>
      <td class="age">...</td>
    </tr>
    
You can also specify ``attrs`` attribute when creating a column. django-tables2
supports 3 different dictionaries, this way you can give different attributes
to column tags in table header (``th``), rows (``td``) or footer (``tf``)

.. sourcecode:: python

    >>> import django_tables2 as tables
    >>>
    >>> class SimpleTable(tables.Table):
    ...     id = tables.Column(attrs={'td': {'class': 'my-class'}})
    ...     age = tables.Column(attrs={'tf': {'bgcolor': 'red'}})
    ...
    ...     class Meta:
    ...         attrs = {'class': 'mytable'}
    ...
    >>> table = SimpleTable()
    >>> # renders to something like this:
    '<tr><td class="my-class">...</td></tr>'
    >>> # and the footer will look like this:
    '<tfoot><tr> ... <td class="age" bgcolor="red"></tr></tfoot>''


.. _custom-template:

Custom Template
---------------

And of course if you want full control over the way the table is rendered,
ignore the built-in generation tools, and instead pass an instance of your
`.Table` subclass into your own template, and render it yourself.

Have a look at the ``django_tables2/table.html`` template for an example.

You can set `DJANGO_TABLES2_TEMPLATE` in your django settings to change the
default template django-tables2 looks for.
