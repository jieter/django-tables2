.. _table-data:

Populating a table with data
============================

Tables are compatible with a range of input data structures. If you've seen the
tutorial you'll have seen a queryset being used, however any iterable that
supports :func:`len` and contains items that expose key-based accessed to
column values is fine.

An an example we'll demonstrate using list of dicts. When defining a table it's
necessary to declare each column. If your data matches the fields in a model,
columns can be declared automatically for you via the `Table.Meta.model`
option, but for non-queryset data you'll probably want to declare
them manually::

    import django_tables2 as tables

    data = [
        {'name': 'Bradley'},
        {'name': 'Stevie'},
    ]

    class NameTable(tables.Table):
        name = tables.Column()

    table = NameTable(data)

You can use this technique to override columns that were automatically created
via `Table.Meta.model` too::

    # models.py
    from django.db import models

    class Person(models.Model):
        name = models.CharField(max_length=200)


    # tables.py
    import django_tables2 as tables
    from .models import Person

    class PersonTable(tables.Table):
        name = tables.Column(verbose_name='full name')

        class Meta:
            model = Person
