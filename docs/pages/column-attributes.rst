.. _column-attributes:

Column attributes
=================

Column attributes can be specified using the `dict` with specific keys.
The dict defines HTML attributes for one of more elements within the column.
Depending on the column, different elements are supported, however ``th``,
``td``, and ``cell`` are supported universally.

e.g.

.. sourcecode:: python

    >>> import django_tables2 as tables
    >>>
    >>> class SimpleTable(tables.Table):
    ...     name = tables.Column(attrs={"th": {"id": "foo"}})
    ...
    >>> # will render something like this:
    '{snip}<thead><tr><th id="foo" class="name">{snip}<tbody><tr><td class="name">{snip}'


For ``th`` and ``td``, the column name will be added as a class name. This makes
selecting the row for styling easier.
Have a look at each column's API reference to find which elements are supported.
