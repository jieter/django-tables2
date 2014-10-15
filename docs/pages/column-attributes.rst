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
    >>> SimpleTable(data).as_html()
    "{snip}<thead><tr><th id="foo" class="name">{snip}<tbody><tr><td class="name">{snip}"


``th`` and ``td`` are special cases because they're extended during rendering
to add the column name as a class. This is done to make writing CSS easier.
Have a look at each column's API reference to find which elements are
supported.

