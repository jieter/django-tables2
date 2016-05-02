Glossary
========

.. glossary::

    accessor
        Refers to an `.Accessor` object

    column name
        The name given to a column. In the follow example, the *column name* is
        ``age``.

        .. sourcecode:: python

            class SimpleTable(tables.Table):
                age = tables.Column()

    empty value
        An empty value is synonymous with "no value". Columns have an
        ``empty_values`` attribute that contains values that are considered
        empty. It's a way to declare which values from the database correspond
        to *null*/*blank*/*missing* etc.

    order by alias
        A prefixed column name that describes how a column should impact the
        order of data within the table. This allows the implementation of how
        a column affects ordering to be abstracted, which is useful (e.g. in
        querystrings).

        .. sourcecode:: python

            class ExampleTable(tables.Table):
                name = tables.Column(order_by=('first_name', 'last_name'))

        In this example ``-name`` and ``name`` are valid order by aliases. In
        a querystring you might then have ``?order=-name``.

    table
        The traditional concept of a table. i.e. a grid of rows and columns
        containing data.

    view
        A Django view.

    record
        A single Python object used as the data for a single row.

    render
        The act of serializing a `.Table` into
        HTML.

    template
        A Django template.

    table data
        An interable of :term:`records <record>` that
        `.Table` uses to populate its rows.
