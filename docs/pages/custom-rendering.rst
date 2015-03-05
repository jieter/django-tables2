.. _custom-rendering:

Custom rendering
================

Various options are available for changing the way the table is :term:`rendered
<render>`. Each approach has a different balance of ease-of-use and
flexibility.


.. _table.render_foo:

:meth:`Table.render_FOO` methods
--------------------------------

To change how a column is rendered, implement a ``render_FOO`` method on the
table (where ``FOO`` is the :term:`column name`). This approach is suitable if
you have a one-off change that you don't want to use in multiple tables.

Supported keyword arguments include:

- ``record`` -- the entire record for the row from the :term:`table data`
- ``value`` -- the value for the cell retrieved from the :term:`table data`
- ``column`` -- the `.Column` object
- ``bound_column`` -- the `.BoundColumn` object
- ``bound_row`` -- the `.BoundRow` object
- ``table`` -- alias for ``self``

Here's an example where the first column displays the current row number::

    >>> import django_tables2 as tables
    >>> import itertools
    >>> class SimpleTable(tables.Table):
    ...     row_number = tables.Column(empty_values=())
    ...     id = tables.Column()
    ...     age = tables.Column()
    ...
    ...     def __init__(self, *args, **kwargs):
    ...         super(SimpleTable, self).__init__(*args, **kwargs)
    ...         self.counter = itertools.count()
    ...
    ...     def render_row_number(self):
    ...         return 'Row %d' % next(self.counter)
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

Python's `inspect.getargspec` is used to only pass the arguments declared by the
function. This means it's not necessary to add a catch all (``**``) keyword
argument.

.. important::

    `render` methods are *only* called if the value for a cell is determined to
    be not an :term:`empty value`. When a value is in `.Column.empty_values`,
    a default value is rendered instead (both `.Column.render` and
    ``Table.render_FOO`` are skipped).

.. _subclassing-column:

Subclassing `.Column`
---------------------

Defining a column subclass allows functionality to be reused across tables.
Columns have a `render` method that behaves the same as :ref:`table.render_foo`
methods on tables::

    >>> import django_tables2 as tables
    >>>
    >>> class UpperColumn(tables.Column):
    ...     def render(self, value):
    ...         return value.upper()
    ...
    >>> class Example(tables.Table):
    ...     normal = tables.Column()
    ...     upper = UpperColumn()
    ...
    >>> data = [{'normal': 'Hi there!',
    ...          'upper':  'Hi there!'}]
    ...
    >>> table = Example(data)
    >>> table.as_html()
    u'<table><thead><tr><th>Normal</th><th>Upper</th></tr></thead><tbody><tr><td>Hi there!</td><td>HI THERE!</td></tr></tbody></table>\n'

See :ref:`table.render_foo` for a list of arguments that can be accepted.

For complicated columns, you may want to return HTML from the
:meth:`~Column.render` method. This is fine, but be sure to mark the string as
safe to avoid it being escaped::

    >>> from django.utils.safestring import mark_safe
    >>> from django.utils.html import escape
    >>>
    >>> class ImageColumn(tables.Column):
    ...     def render(self, value):
    ...         return mark_safe('<img src="/media/img/%s.jpg" />'
    ...                          % escape(value))
    ...


.. _css:

CSS
---

In order to use CSS to style a table, you'll probably want to add a
``class`` or ``id`` attribute to the ``<table>`` element. django-tables2 has
a hook that allows abitrary attributes to be added to the ``<table>`` tag.

.. sourcecode:: python

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

.. _custom-template:

Custom Template
---------------

And of course if you want full control over the way the table is rendered,
ignore the built-in generation tools, and instead pass an instance of your
`.Table` subclass into your own template, and render it yourself.

Have a look at the ``django_tables2/table.html`` template for an example.

