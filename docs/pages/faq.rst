.. _faq:

FAQ
===

Some frequently requested questions/examples. All examples assume you
import djang-tables2 like this::

    import django_tables2 as tables

How to create a row counter?
----------------------------

You can use `itertools.counter` to add row count to a table. Note that in a
paginated table, every page's counter will start at zero.

Use a `render_counter()`-method::

    import itertools

    class CountryTable(tables.Table):
        counter = tables.Column(empty_values=(), orderable=False)

        def render_counter(self):
            self.row_counter = getattr(self, 'row_counter', itertools.count())
            return next(self.row_counter)



Or create a specialized column::

    import itertools

    class CounterColumn(tables.Column):
        def __init__(self, *args, **kwargs):
            self.counter = itertools.count()
            kwargs.update({
                'empty_values': (),
                'orderable': False
            })
            super(CounterColumn, self).__init__(*args, **kwargs)

        def render(self):
            return next(self.counter)


How to add a footer containing a column total?
----------------------------------------------

Using the `footer`-argument to `~.Column`::

    class CountryTable(tables.Table):
        population = tables.Column(
            footer=lambda table: sum(x['population'] for x in table.data)
        )

Or by creating a custom column::

    class SummingColumn(tables.Column):
        def render_footer(self, bound_column, table):
            return sum(bound_column.accessor.resolve(row) for row in table.data)

    class Table(tables.Table):
        name = tables.Column(footer='Total:')
        population = SummingColumn()

Documentation: :ref:`column-footers`

.. note ::
    You table template must include a block rendering the table footer!
