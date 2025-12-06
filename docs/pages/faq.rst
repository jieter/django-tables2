.. _faq:

..
    Any code examples in this file should have a corresponding test in
    tests/test_faq.py

FAQ
===

Some frequently requested questions/examples. All examples assume you
import django-tables2 like this::

    import django_tables2 as tables

How should I fix error messages about the request context processor?
--------------------------------------------------------------------

The error message looks something like this::

    Tag {% qs_replace %} requires django.template.context_processors.request to be
    in the template configuration in settings.TEMPLATES[]OPTIONS.context_processors)
    in order for the included template tags to function correctly.

which should be pretty clear, but here is an example template configuration anyway::

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": ["templates"],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.contrib.auth.context_processors.auth",
                    "django.template.context_processors.request",
                    "django.template.context_processors.static",
                ],
            }
        }
    ]

How to create a row counter?
----------------------------

You can use ``itertools.counter`` to add row count to a table. Note that in a
paginated table, every page's counter will start at zero::

    class CountryTable(tables.Table):
        counter = tables.TemplateColumn("{{ row_counter }}")


How to add a footer containing a column total?
----------------------------------------------

Using the `footer`-argument to `~.Column`::

    class CountryTable(tables.Table):
        population = tables.Column(
            footer=lambda table: sum(x["population"] for x in table.data)
        )

Or by creating a custom column::

    class SummingColumn(tables.Column):
        def render_footer(self, bound_column, table):
            return sum(bound_column.accessor.resolve(row) for row in table.data)

    class Table(tables.Table):
        name = tables.Column(footer="Total:")
        population = SummingColumn()

Documentation: :ref:`column-footers`

.. note ::
    Your table template must include a block rendering the table footer!


Can I use inheritance to build Tables that share features?
----------------------------------------------------------

Yes, like this::

    class CountryTable(tables.Table):
        name = tables.Column()
        language = tables.Column()

A `CountryTable` will show columns `name` and `language`::

    class TouristCountryTable(CountryTable):
        tourist_info = tables.Column()

A `TouristCountryTable` will show columns `name`, `language` and `tourist_info`.

Overwriting a `Column` attribute from the base class with anything that is not a
`Column` will result in removing that Column from the `Table`. For example::

    class SimpleCountryTable(CountryTable):
        language = None

A `SimpleCountryTable` will only show column `name`.


How can I use with Jinja2 template?
-----------------------------------

In Jinja2 templates, the ``{% render_table %}`` tag is not available, but you can still use *django-tables2* like this::

    {{ table.as_html(request) }}

where ``request`` need to be passed from view, or from *context processors* (which is supported by `django-jinja <https://niwinz.github.io/django-jinja/latest/#_context_processors_support>`_).
