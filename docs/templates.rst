===================
Rendering the table
===================

A table instance bound to data has two attributes ``columns`` and ``rows``,
which can be iterate over:

.. code-block:: django

    <table>
    <tr>
        {% for column in table.columns %}
        <th><a href="?sort={{ column.name_toggled }}">{{ column }}</a></th>
        {% endfor %}
    </tr>
    {% for row in table.rows %}
        <tr>
        {% for value in row %}
            <td>{{ value }}</td>
        {% endfor %}
        </tr>
    {% endfor %}
    </table>

For the attributes available on a bound column, see :doc:`features/index`,
depending on what you want to accomplish.


Custom render methods
---------------------

Often, displaying a raw value of a table cell is not good enough. For
example, if your table has a ``rating`` column, you might want to show
an image showing the given number of **stars**, rather than the plain
numeric value.

While you can always write your templates so that the column in question
is treated separately, either by conditionally checking for a column name,
or by explicitely rendering each column manually (as opposed to simply
looping over the ``rows`` and ``columns`` attributes), this is often
tedious to do.

Instead, you can opt to move certain formatting responsibilites into
your Python code:

.. code-block:: django

    class BookTable(tables.ModelTable):
        name = tables.Column()
        rating_int = tables.Column(name="rating")

        def render_rating(self, instance):
            if instance.rating_count == 0:
                return '<img ="no-rating.png">'
            else:
                return '<img ="rating-%s.png">' % instance.rating_int

When accessing ``table.rows[i].rating``, the ``render_rating`` method
will be called. Note the following:

   - What is passed is underlying raw data object, in this case, the
     model instance. This gives you access to data values that may not
     have been defined as a column.
   - For the method name, the public name of the column must be used, not
     the internal field name. That is, it's ``render_rating``, not
     ``render_rating_int``.
   - The method is called whenever the cell value is retrieved by you,
     whether from Python code or within templates. However, operations by
     ``django-tables``, like sorting, always work with the raw data.


The table.columns container
---------------------------

While you can iterate through the ``columns`` attribute and get all the
currently visible columns, it further provides features that go beyond
a simple iterator.

You can access all columns, regardless of their visibility, through
``columns.all``.

``columns.sortable`` is a handy shortcut that exposes all columns which's
``sortable`` attribute is True. This can be very useful in templates, when
doing {% if column.sortable %} can conflict with {{ forloop.last }}.


Template Utilities
------------------

If you want the give your users the ability to interact with your table (e.g.
change the ordering), you will need to create urls with the appropriate
queries. To simplify that process, django-tables comes with a helpful
templatetag:

.. code-block:: django

    {% set_url_param sort="name" %}       # ?sort=name
    {% set_url_param sort="" %}           # delete "sort" param

The template library can be found in 'django_modules.app.templates.tables'.
If you add ''django_modules.app' to your ``INSTALLED_APPS`` setting, you
will be able to do:

.. code-block:: django

    {% load tables %}

Note: The tag requires the current request to be available as ``request``
in the context (usually, this means activating the Django request context
processor).
