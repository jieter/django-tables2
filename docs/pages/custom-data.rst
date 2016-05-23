.. _accessors:

Alternative column data
=======================

Various options are available for changing the way the table is :term:`rendered
<render>`. Each approach has a different balance of ease-of-use and
flexibility.


Using `~.Accessors`
-------------------

Each column has a 'key' that describes which value to pull from each record to
populate the column's cells. By default, this key is just the name given to the
column, but it can be changed to allow foreign key traversal or other complex
cases.

To reduce ambiguity, rather than calling it a 'key', we use the name 'accessor'.

Accessors are just dotted paths that describe how an object should be traversed
to reach a specific value, for example::

    >>> from django_tables2 import A
    >>> data = {'abc': {'one': {'two': 'three'}}}
    >>> A('abc.one.two').resolve(data)
    'three'

Dots represent a relationships, and are attempted in this order:

1. Dictionary lookup ``a[b]``
2. Attribute lookup ``a.b``
3. List index lookup ``a[int(b)]``

If the resulting value is callable, it is called and the return value is used.

.. _table.render_foo:

`Table.render_foo` methods
------------------------------------

To change how a column is rendered, define a ``render_foo`` method on
the table for example: `render_row_number()` for a column named `row_number`.
This approach is suitable if you have a one-off change that you do not want to
use in multiple tables.

Supported keyword arguments include:

- ``record`` -- the entire record for the row from the :term:`table data`
- ``value`` -- the value for the cell retrieved from the :term:`table data`
- ``column`` -- the `.Column` object
- ``bound_column`` -- the `.BoundColumn` object
- ``bound_row`` -- the `.BoundRow` object
- ``table`` -- alias for ``self``

This example shows how to render the row number in the first row::

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
    >>> print ', '.join(map(str, table.rows[0]))
    Row 0, <10>, 31

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
    >>> # renders to something like this:
    '''<table>
        <thead><tr><th>Normal</th><th>Upper</th></tr></thead>
        <tbody><tr><td>Hi there!</td><td>HI THERE!</td></tr></tbody>
    </table>'''

See :ref:`table.render_foo` for a list of arguments that can be accepted.

For complicated columns, you may want to return HTML from the
:meth:`~Column.render` method. Make sure to use Django's html formatting functions::

    >>> from django.utils.html import format_html
    >>>
    >>> class ImageColumn(tables.Column):
    ...     def render(self, value):
    ...         return format_html('<img src="/media/img/{}.jpg" />', value)
    ...
