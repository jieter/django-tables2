Table Mixins
============

It's possible to create a mixin for a table that overrides something, however
unless it itself is a subclass of `.Table` class variable instances of
`.Column` will **not** be added to the class which is using the mixin.

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
`~django_tables2.tables.Table`. With this in mind the previous example
*should* have been written as follows::

    >>> class UsefulMixin(tables.Table):
    ...     extra = tables.Column()
    ...
    >>> class TestTable(UsefulMixin, tables.Table):
    ...     name = tables.Column()
    ...
    >>> TestTable.base_columns.keys()
    ['extra', 'name']

