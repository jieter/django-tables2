Class Based Generic Mixins
==========================

Django-tables2 comes with two class based view mixins: `.SingleTableMixin` and
`.MultiTableMixin`.


A single table using `.SingleTableMixin`
----------------------------------------

`.SingleTableMixin` makes it trivial to incorporate a table into a view or
template.

The following view parameters are supported:

- ``table_class`` –- the table class to use, e.g. ``SimpleTable``
- ``table_data`` (or ``get_table_data()``) -- the data used to populate the table
- ``context_table_name`` -- the name of template variable containing the table object
- ``table_pagination`` (or ``get_table_pagination``) -- pagination
  options to pass to `.RequestConfig`. Set ``table_pagination=False``
  to disable pagination.
- ``get_table_kwargs()`` allows the keyword arguments passed to the ``Table``
   constructor.

For example::

    from django_tables2 import SingleTableView


    class Person(models.Model):
        first_name = models.CharField(max_length=200)
        last_name = models.CharField(max_length=200)


    class PersonTable(tables.Table):
        class Meta:
            model = Person


    class PersonList(SingleTableView):
        model = Person
        table_class = PersonTable


The template could then be as simple as:

.. sourcecode:: django

    {% load render_table from django_tables2 %}
    {% render_table table %}

Such little code is possible due to the example above taking advantage of
default values and `.SingleTableMixin`'s eagerness at finding data sources
when one isn't explicitly defined.

.. note::

    You don't have to base your view on `ListView`, you're able to mix
    `SingleTableMixin` directly.


Multiple tables using `.MultiTableMixin`
--------------------------------------------

If you need more than one table in a single view you can use `MultiTableMixin`.
It manages multiple tables for you and takes care of adding the appropriate
prefixes for them. Just define a list of tables in the tables attribute::

    from django_tables2 import MultiTableMixin
    from django.views.generic.base import TemplateView

    class PersonTablesView(MultiTableMixin, TemplateView):
        template_name = 'multiTable.html'
        tables = [
            PersonTable(qs),
            PersonTable(qs, exclude=('country', ))
        ]

        table_pagination = {
            'per_page': 10
        }

In the template, you get a variable `tables`, which you can loop over like this:

.. sourcecode:: django

    {% for table in tables %}
        {% render_table table %}
    {% endfor %}
