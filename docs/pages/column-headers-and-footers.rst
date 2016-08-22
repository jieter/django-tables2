.. _column-headers-and-footers:

Customizing headers and footers
===============================

By default an header and no footer will be rendered.


Adding column headers
---------------------

The header cell for each column comes from `~.Column.header`. By default this
method returns `~.Column.verbose_name`, falling back to the titlised attribute
name of the column in the table class.

When using queryset data and a verbose name hasn't been explicitly defined for
a column, the corresponding model field's `verbose_name` will be used.

Consider the following:

    >>> class Region(models.Model):
    ...     name = models.CharField(max_length=200)
    ...
    >>> class Person(models.Model):
    ...     first_name = models.CharField(verbose_name='model verbose name', max_length=200)
    ...     last_name = models.CharField(max_length=200)
    ...     region = models.ForeignKey('Region')
    ...
    >>> class PersonTable(tables.Table):
    ...     first_name = tables.Column()
    ...     ln = tables.Column(accessor='last_name')
    ...     region_name = tables.Column(accessor='region.name')
    ...
    >>> table = PersonTable(Person.objects.all())
    >>> table.columns['first_name'].header
    'Model Verbose Name'
    >>> table.columns['ln'].header
    'Last Name'
    >>> table.columns['region_name'].header
    'Name'

As you can see in the last example (region name), the results are not always
desirable when an accessor is used to cross relationships. To get around this
be careful to define `.Column.verbose_name`.

.. _ordering-class-name:

Changing class names for ordered column headers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When a column is ordered in an ascending state there needs to be a way to show
it in the interface. django-tables2 does this by adding an `asc` class for
ascending or a `desc` class for descending. It should also be known that any
orderable column is added with an `orderable` class to the column header.

Sometimes there may be a need to change these default classes.

On the `attrs` attribute of the table, you can add a `th` key with the value of
a dictionary. Within that `th` dictionary, you may add an `_ordering` key also
with the value of a dictionary.

The `_ordering` element is optional and all elements within it are optional.
Inside you can have an `orderable` element, which will change the default
`orderable` class name. You can also have `ascending` which will will change the
default `asc` class name. And lastly, you can have `descending` which will
change the default `desc` class name.

Example::

    class Table(tables.Table):
        Meta:
            attrs = {
                'th' : {
                    '_ordering': {
                        'orderable': 'sortable', # Instead of `orderable`
                        'ascending': 'ascend',   # Instead of `asc`
                        'descending': 'descend'  # Instead of `desc`
                    }
                }
            }


It can also be specified at initialization using the `attrs` for both: table and
column::

    ATTRIBUTES = {
        'th' : {
            '_ordering': {
                'orderable': 'sortable', # Instead of `orderable`
                'ascending': 'ascend',   # Instead of `asc`
                'descending': 'descend'  # Instead of `desc`
            }
        }
    }

    table = tables.Table(queryset, attrs=ATTRIBUTES)

    # OR

    class Table(tables.Table):
        my_column = tables.Column(attrs=ATTRIBUTES)


.. _column-footers:

Adding column footers
---------------------

By default, no footer will be rendered. If you want to add a footer, define a
footer on at least one column.

That will make the table render a footer on every view of the table. It's up to
you to decide if that makes sense if your table is paginated.

Pass `footer`-argument to the `~.Column` constructor.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The simplest case is just passing a `str` as the footer argument to a column::

    country = tables.Column(footer='Total:')

This will just render the string in the footer. If you need to do more complex
things, like showing a sum or an average, you can pass a callable::

    population = tables.Column(
        footer=lambda table: sum(x['population'] for x in table.data)
    )

You can expect `table`, `column` and `bound_column` as argument.

Define `render_footer` on a custom column.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you need the same footer in multiple columns, you can create your own custom
column. For example this column that renders the sum of the values in the column::

    class SummingColumn(tables.Column):
        def render_footer(self, bound_column, table):
            return sum(bound_column.accessor.resolve(row) for row in table.data)


Then use this column like so::

    class Table(tables.Table):
        name = tables.Column()
        country = tables.Column(footer='Total:')
        population = SummingColumn()


.. note::

    If you are `sum`\ ming over tables with big datasets, chances are it's going
    to be slow. You should use some database aggregation function instead.
