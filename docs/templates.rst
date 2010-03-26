================================
Rendering the table in templates
================================


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


The table.columns container
---------------------------

While you can iterate through ``columns`` and get all the currently visible
columns, it further provides features that go beyond a simple iterator.

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
