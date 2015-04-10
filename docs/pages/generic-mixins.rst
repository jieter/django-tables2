Class Based Generic Mixins
==========================

Django 1.3 introduced `class based views`__ as a mechanism to reduce the
repetition in view code. django-tables2 comes with a single class based view
mixin: `.SingleTableMixin`. It makes it trivial to incorporate a table into a
view/template.

The following view parameters are supported:

- ``table_class`` –- the table class to use, e.g. ``SimpleTable``
- ``table_data`` (or ``get_table_data()``) -- the data used to populate the table
- ``context_table_name`` -- the name of template variable containing the table object
- ``table_pagination`` (or ``get_table_pagination``) -- pagination
  options to pass to `.RequestConfig`. Set ``table_pagination=False``
  to disable pagination.

.. __: https://docs.djangoproject.com/en/1.3/topics/class-based-views/

For example:

.. sourcecode:: python

    from django_tables2 import SingleTableView


    class Person(models.Model):
        first_name = models.CharField(max_length=200)
        last_name = models.CharField(max_length=200)


    class PersonTable(tables.Table):
        class Meta:
            model = Simple


    class PersonList(SingleTableView):
        model = Person
        table_class = PersonTable


The template could then be as simple as:

.. sourcecode:: django

    {% load render_table from django_tables2 %}
    {% render_table table %}

Such little code is possible due to the example above taking advantage of
default values and `.SimpleTableMixin`'s eagarness at finding data sources
when one isn't explicitly defined.

.. note::

    If you need more than one table on a page, use `.SingleTableView` and use
    `.get_context_data` to initialise the other tables and add them to the
    context.

.. note::

    You don't have to base your view on `ListView`, you're able to mix
    `SingleTableMixin` directly.

