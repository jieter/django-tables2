=================
All about Columns
=================

Columns are what defines a table. Therefore, the way you configure your
columns determines to a large extend how your table operates.

``django_tables.columns`` currently defines three classes, ``Column``,
``TextColumn`` and ``NumberColumn``. However, the two subclasses currently
don't do anything special at all, so you can simply use the base class.
While this will likely change in the future (e.g. when grouping is added),
the base column class will continue to work by itself.

There are no required arguments. The following is fine:

.. code-block:: python

    class MyTable(tables.MemoryTable):
        c = tables.Column()

It will result in a column named ``c`` in the table. You can specify the
``name`` to override this:

.. code-block:: python

    c = tables.Column(name="count")

The column is now called and accessed via "count", although the table will
still use ``c`` to read it's values from the source. You can however modify
that as well, by specifying ``data``:

.. code-block:: python

    c = tables.Column(name="count", data="count")

For practicual purposes, ``c`` is now meaningless. While in most cases
you will just define your column using the name you want it to have, the
above is useful when working with columns automatically generated from
models:

.. code-block:: python

    class BookTable(tables.ModelTable):
        book_name = tables.Column(name="name")
        author = tables.Column(data="info__author__name")
        class Meta:
            model = Book

The overwritten ``book_name`` field/column will now be exposed as the
cleaner ``name``, and the new ``author`` column retrieves it's values from
``Book.info.author.name``.

Apart from their internal name, you can define a string that will be used
when for display via ``verbose_name``:

.. code-block:: python

    pubdate = tables.Column(verbose_name="Published")

The verbose name will be used, for example, if you put in a template:

.. code-block:: django

    {{ column }}

If you don't want a column to be sortable by the user:

.. code-block:: python

    pubdate = tables.Column(sortable=False)

Sorting is also affected by ``direction``, which can be used to change the
*default* sort direction to descending. Note that this option only indirectly
translates to the actual direction. Normal und reverse order, the terms
django-tables exposes, now simply mean different things.

.. code-block:: python

    pubdate = tables.Column(direction='desc')

If you don't want to expose a column (but still require it to exist, for
example because it should be sortable nonetheless):

.. code-block:: python

    pubdate = tables.Column(visible=False)

The column and it's values will now be skipped when iterating through the
table, although it can still be accessed manually.

Finally, you can specify default values for your columns:

.. code-block:: python

    health_points = tables.Column(default=100)

Note that how the default is used and when it is applied differs between
table types.
