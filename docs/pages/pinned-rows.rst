.. _pinned_rows:

Pinned rows
===========

This feature allows one to pin certain rows to the top or bottom of your table.
Provide an implementation for one or two of these methods, returning an iterable
(QuerySet, list of dicts, list objects) representing the pinned data:

* `get_top_pinned_data(self)` - Displays the returned rows on top.
* `get_bottom_pinned_data(self)` - Displays the returned rows at the bottom.

Pinned rows are not affected by sorting and pagination, they will be present on every
page of the table, regardless of ordering.
Values will be rendered just like you are used to for normal rows.

Example::

    class Table(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()

        def get_top_pinned_data(self):
            return [
                {'first_name': 'Janet', 'last_name': 'Crossen'},
                # key 'last_name' is None here, so the default value will be rendered.
                {'first_name': 'Trine', 'last_name': None}
            ]

.. note:: If you need very different rendering for the bottom pinned rows, chances are
          you actually want to use column footers: :ref:`column-footers`

.. _pinned_row_attributes:

Attributes for pinned rows
~~~~~~~~~~~~~~~~~~~~~~~~~~

You can override the attributes used to render the ``<tr>`` tag of the pinned rows using: ``pinned_row_attrs``.
This works exactly like :ref:`row-attributes`.

.. note:: By default the ``<tr>`` tags for pinned rows will get the attribute ``class="pinned-row"``.

    .. sourcecode:: django

        <tr class="odd pinned-row" ...> [...] </tr>
        <tr class="even pinned-row" ...> [...] </tr>
