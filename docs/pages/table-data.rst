.. _table-data:

Populating a table with data
============================

Tables can be created from a range of input data structures. If you've seen the
tutorial you'll have seen a queryset being used, however any iterable that
supports :func:`len` and contains items that expose key-based access to column
values is fine.


List of dicts
-------------

An an example we will demonstrate using list of dicts. When defining a table
it is necessary to declare each column::

    import django_tables2 as tables

    data = [
        {'name': 'Bradley'},
        {'name': 'Stevie'},
    ]

    class NameTable(tables.Table):
        name = tables.Column()

    table = NameTable(data)


Querysets
---------

If you build use tables to display `~django.db.models.query.QuerySet` data,
rather than defining each column manually in the table, the `.Table.Meta.model`
option allows tables to be dynamically created based on a model::

    # models.py
    class Person(models.Model):
        first_name = models.CharField(max_length=200)
        last_name = models.CharField(max_length=200)
        user = models.ForeignKey('auth.User')
        dob = models.DateField()

    # tables.py
    import django_tables2 as tables

    class PersonTable(tables.Table):
        class Meta:
            model = Person

    # views.py
    def person_list(request):
        table = PersonTable(Person.objects.all())

        return render(request, 'person_list.html', {
            'table': table
        })

This has a number of benefits:

- Less repetition
- Column headers are defined using the field's `~.models.Field.verbose_name`
- Specialized columns are used where possible (e.g. `.DateColumn` for a
  `~.models.DateField`)

When using this approach, the following options might be useful to customize
what fields to show or hide:

- `~.Table.Meta.sequence` -- reorder columns
- `~.Table.Meta.fields` -- specify model fields to *include*
- `~.Table.Meta.exclude` -- specify model fields to *exclude*
