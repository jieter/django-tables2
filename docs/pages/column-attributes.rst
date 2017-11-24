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

Callables passed in this dict will be called, with optional kwargs ``table``,
``bound_column`` ``record`` and ``value``, with the return value added. For example::

    class Table(tables.Table):
        person = tables.Column(attrs={
            'td': {
                'data-length': lambda value: len(value)
            }
        })

will render the ``<td>``'s in the tables ``<body>`` with a ``data-length`` attribute
containing the number of characters in the value.

.. note::
    The kwargs ``record`` and ``value`` only make sense in the context of a row
    containing data. If you supply a callable with one of these keyword arguments,
    it will not be executed for the header and footer rows.

    If you also want to customize the attributes of those tags, you must define a
    callable with a catchall (``**kwargs``) argument::

        def data_first_name(**kwargs):
            first_name = kwargs.get('first_name', None)
            if first_name is None:
                return 'header'
            else:
                return first_name

        class Table(tables.Table):
            first_name = tables.Column(attrs={
                'td': {
                    'data-first-name': data_first_name
                }
            })

This `attrs` can also be defined when subclassing a column, to allow better reuse::

    class PersonColumn(tables.Column):
        attrs = {
            'td': {
                'data-first-name': lambda record: record.first_name
                'data-last-name': lambda record: record.last_name
            }
        }
        def render(self, record):
            return '{} {}'.format(record.first_name, record.last_name)

    class Table(tables.Table):
        person = PersonColumn()

is equivalent to the previous example.

.. _row-attributes:

Row attributes
~~~~~~~~~~~~~~

Row attributes can be specified using a dict defining the HTML attributes for
the ``<tr>`` element on each row. The values of the dict may be

By default, class names *odd* and *even* are supplied to the rows, wich can be
customized using the ``row_attrs`` `.Table.Meta` attribute or as argument to the
constructor of `.Table`. String-like values will just be added,
callables will be called with optional keyword argument `record`, the return value
will be added. For example::

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
