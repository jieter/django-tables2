.. _column-attributes:

Column and row attributes
=========================

Column attributes
~~~~~~~~~~~~~~~~~

Column attributes can be specified using the `dict` with specific keys.
The dict defines HTML attributes for one of more elements within the column.
Depending on the column, different elements are supported, however ``th``,
``td``, and ``cell`` are supported universally::

    >>> import django_tables2 as tables
    >>>
    >>> class SimpleTable(tables.Table):
    ...     name = tables.Column(attrs={'th': {'id': 'foo'}})
    ...
    >>> # will render something like this:
    '{snip}<thead><tr><th id="foo" class="name">{snip}<tbody><tr><td class="name">{snip}'


For ``th`` and ``td``, the column name will be added as a class name. This makes
selecting the row for styling easier.
Have a look at each column's API reference to find which elements are supported.


.. _row-attributes:

Row attributes
~~~~~~~~~~~~~~

Row attributes can be specified using a dict defining the HTML attributes for
the ``<tr>`` element on each row. The values of the dict may be

By default, class names *odd* and *even* are supplied to the rows, wich can be
customized using the ``row_attrs`` `.Table.Meta` attribute or as argument to the
constructor of `.Table`, for example::

    class Table(tables.Table):
        class Meta:
            model = User
            row_attrs = {
                'data-id': lambda record: record.pk
            }

will render tables with the following ``<tr>`` tag

.. sourcecode:: django

    <tr class="odd" data-id="1"> [...] </tr>
    <tr class="even" data-id="2"> [...] </tr>
