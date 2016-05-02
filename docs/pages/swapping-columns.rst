.. _swapping-columns:

Swapping the position of columns
================================

By default columns are positioned in the same order as they are declared,
however when mixing auto-generated columns (via `Table.Meta.model`) with
manually declared columns, the column sequence becomes ambiguous.

To resolve the ambiguity, columns sequence can be declared via the
`.Table.Meta.sequence` option::

    class PersonTable(tables.Table):
        selection = tables.CheckBoxColumn(accessor='pk', orderable=False)

        class Meta:
            model = Person
            sequence = ('selection', 'first_name', 'last_name')

The special value ``'...'`` can be used to indicate that any omitted columns
should inserted at that location. As such it can be used at most once.
