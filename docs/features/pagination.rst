----------
Pagination
----------

If your table has a large number of rows, you probably want to paginate
the output. There are two distinct approaches.

First, you can just paginate over ``rows`` as you would do with any other
data:

.. code-block:: python

    table = MyTable(queryset)
    paginator = Paginator(table.rows, 10)
    page = paginator.page(1)

You're not necessarily restricted to Django's own paginator (or subclasses) -
any paginator should work with this approach, so long it only requires
``rows`` to implement ``len()``, slicing, and, in the case of a
``ModelTable``, a ``count()`` method. The latter means that the
``QuerySetPaginator`` also works as expected.

Alternatively, you may use the ``paginate`` feature:

.. code-block:: python

    table = MyTable(queryset)
    table.paginate(Paginator, 10, page=1, orphans=2)
    for row in table.rows.page():
        pass
    table.paginator                # new attributes
    table.page

The table will automatically create an instance of ``Paginator``,
passing it's own data as the first argument and additionally any arguments
you have specified, except for ``page``. You may use any paginator, as long
as it follows the Django protocol:

* Take data as first argument.
* Support a page() method returning an object with an ``object_list``
  attribute, exposing the paginated data.

Note that due to the abstraction layer that ``django-tables`` represents, it
is not necessary to use Django's ``QuerySetPaginator`` with model tables.
Since the table knows that it holds a queryset, it will automatically choose
to use count() to determine the data length (which is exactly what
``QuerySetPaginator`` would do).