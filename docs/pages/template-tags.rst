.. _template_tags:

Template tags
=============

.. _template-tags.render_table:

render_table
------------

Renders a `~django_tables2.tables.Table` object to HTML and enables as
many features in the output as possible.

.. sourcecode:: django

    {% load django_tables2 %}
    {% render_table table %}

    {# Alternatively a specific template can be used #}
    {% render_table table "path/to/custom_table_template.html" %}

If the second argument (template path) is given, the template will be rendered
with a `.RequestContext` and the table will be in the variable ``table``.

.. note::

    This tag temporarily modifies the `.Table` object during rendering. A
    ``context`` attribute is added to the table, providing columns with access
    to the current context for their own rendering (e.g. `.TemplateColumn`).

This tag requires that the template in which it's rendered contains the
`~.http.HttpRequest` inside a ``request`` variable. This can be achieved by
ensuring the ``TEMPLATES[]['OPTIONS']['context_processors']`` setting contains
``django.template.context_processors.request``.
Please refer to the Django documentation for the TEMPLATES-setting_.

.. _TEMPLATES-setting: https://docs.djangoproject.com/en/stable/ref/settings/#std:setting-TEMPLATES

.. _template-tags.querystring:

querystring
-----------

A utility that allows you to update a portion of the query-string without
overwriting the entire thing.

Let's assume we have the querystring ``?search=pirates&sort=name&page=5`` and
we want to update the ``sort`` parameter:

.. sourcecode:: django

    {% querystring "sort"="dob" %}           # ?search=pirates&sort=dob&page=5
    {% querystring "sort"="" %}              # ?search=pirates&page=5
    {% querystring "sort"="" "search"="" %}  # ?page=5

    {% with "search" as key %}               # supports variables as keys
    {% querystring key="robots" %}           # ?search=robots&page=5
    {% endwith %}

This tag requires the ``django.template.context_processors.request`` context
processor, see :ref:`template-tags.render_table`.
