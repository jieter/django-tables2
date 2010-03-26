=================
Sorting the table
=================

``django-tables`` allows you to specify which column the user can sort,
and will validate and resolve an incoming query string value the the
correct ordering.

It will also help you rendering the correct links to change the sort
order in your template.


Specify which columns are sortable
----------------------------------

Tables can take a ``sortable`` option through an inner ``Meta``, the same
concept as known from forms and models in Django:

.. code-block:: python

    class MyTable(tables.MemoryTable):
        class Meta:
            sortable = True

This will be the default value for all columns, and it defaults to ``True``.
You can override the table default for each individual column:

.. code-block:: python

    class MyTable(tables.MemoryTable):
        foo = tables.Column(sortable=False)
        class Meta:
            sortable = True


Setting the table ordering
--------------------------

Your table both takes a ``order_by`` argument in it's constructor, and you
can change the order by assigning to the respective attribute:

.. code-block:: python

    table = MyTable(order_by='-foo')
    table.order_by = 'foo'

You can see that the value expected is pretty much what is used by the
Django database API: An iterable of column names, optionally using a hyphen
as a prefix to indicate reverse order. However, you may also pass a
comma-separated string:

.. code-block:: python

    table = MyTable(order_by='column1,-column2')

When you set ``order_by``, the value is parsed right away, and subsequent
reads will give you the normalized value:

.. code-block:: python

    >>> table.order_by = ='column1,-column2'
    >>> table.order_by
    ('column1', '-column2')

Note: Random ordering is currently not supported.


Error handling
~~~~~~~~~~~~~~

Passing incoming query string values from the request directly to the
table constructor is a common thing to do. However, such data can easily
contain invalid column names, be it that a user manually modified it,
or someone put up a broken link. In those cases, you usually would not want
to raise an exception (nor be notified by Django's error notification
mechanism) - there is nothing you could do anyway.

Because of this, such errors will by default be silently ignored. For
example, if one out of three columns in an "order_by" is invalid, the other
two will still be applied:

.. code-block:: python

    >>> table.order_by = ('name', 'totallynotacolumn', '-date)
    >>> table.order_by
    ('name', '-date)

This ensures that the following table will be created regardless of the
value in ``sort``:

.. code-block:: python

    table = MyTable(data, order_by=request.GET.get('sort'))

However, if you want, you can disable this behaviour and have an exception
raised instead, using:

.. code-block:: python

    import django_tables
    django_tables.options.IGNORE_INVALID_OPTIONS = False


Interacting with order
----------------------

Letting the user change the order of a table is a common scenario. With
respect to Django, this means adding links to your table output that will
send off the appropriate arguments to the server. ``django-tables``
attempts to help with you that.

A bound column, that is a column accessed through a table instance, provides
the following attributes:

- ``name_reversed`` will simply return the column name prefixed with a
  hyphen; this is useful in templates, where string concatenation can
  at times be difficult.

- ``name_toggled`` checks the tables current order, and will then
  return the column either prefixed with an hyphen (for reverse ordering)
  or without, giving you the exact opposite order. If the column is
  currently not ordered, it will start off in non-reversed order.

It is easy to be confused about the difference between the ``reverse`` and
``toggle`` terminology. ``django-tables`` tries to put a normal/reverse-order
abstraction on top of "ascending/descending", where as normal order could
potentially mean either ascending or descending, depending on the column.

Something you commonly see is a table that indicates which column it is
currently ordered by through little arrows. To implement this, you will
find useful:

- ``is_ordered``: Returns ``True`` if the column is in the current
  ``order_by``, regardless of the polarity.

- ``is_ordered_reverse``, ``is_ordered_straight``: Returns ``True`` if the
  column is ordered in reverse or non-reverse, respectively, otherwise
  ``False``.

The above is usually enough for most simple cases, where tables are only
ordered by a single column. For scenarios in which multi-column order is
used, additional attributes are available:

- ``order_by``: Return the current order, but with the current column
  set to normal ordering. If the current column is not already part of
  the order, it is appended. Any existing columns in the order are
  maintained as-is.

- ``order_by_reversed``, ``order_by_toggled``: Similarly, return the
  table's current ``order_by`` with the column set to reversed or toggled,
  respectively. Again, it is appended if not already ordered.

Additionally, ``table.order_by.toggle()`` may also be useful in some cases:
It will toggle all order columns and should thus give you the exact
opposite order.

The following is a simple example of single-column ordering. It shows a list
of sortable columns, each clickable, and an up/down arrow next to the one
that is currently used to sort the table.

.. code-block:: django

    Sort by:
    {% for column in table.columns %}
        {% if column.sortable %}
            <a href="?sort={{ column.name_toggled }}">{{ column }}</a>
            {% if column.is_ordered_straight %}<img src="down.png" />{% endif %}
            {% if column.is_ordered_reverse %}<img src="up.png" />{% endif %}
        {% endif %}
    {% endfor %}
