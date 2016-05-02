.. _tables-for-models:

Tables for models
=================

If you build use tables to display `.QuerySet` data, rather than defining each
column manually in the table, the `.Table.Meta.model` option allows tables to
be dynamically created based on a model::

    # models.py
    class Person(models.Model):
        first_name = models.CharField(max_length=200)
        last_name = models.CharField(max_length=200)
        user = models.ForeignKey("auth.User")
        dob = models.DateField()

    # tables.py
    class PersonTable(tables.Table):
        class Meta:
            model = Person

This has a number of benefits:

- Less code, easier to write, more DRY
- Columns use the field's `~.models.Field.verbose_name`
- Specialized columns are used where possible (e.g. `.DateColumn` for a
  `~.models.DateField`)

When using this approach, the following options are useful:

- `~.Table.Meta.sequence` -- reorder columns
- `~.Table.Meta.fields` -- specify model fields to *include*
- `~.Table.Meta.exclude` -- specify model fields to *exclude*
