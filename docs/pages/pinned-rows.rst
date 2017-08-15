.. _pinned_rows:

Pinned rows
===========

By using Pinned Rows, you can pin particular rows to the top or bottom of your table.
To add pinned rows to your table, you must override `get_top_pinned_data` and/or `get_bottom_pinned_data`
methods in your `.Table` class.

* `get_top_pinned_data(self)` - Display the pinned rows on top.
* `get_bottom_pinned_data(self)` - Display the pinned rows on bottom.

By default both methods return `None` value and pinned rows aren't visible.
Return data for pinned rows should be iterable type like: queryset, list of dicts, list of objects.


Example::

    class Table(tables.Table):

        def get_top_pinned_data(self):
            return [
                # First top pinned row
                {
                    'column_a' : 'value for A column',
                    'column_b' : 'value for B column'
                },
                # Second top pinned row
                {
                    'column_a' : 'extra value for A column'
                    'column_b' : None
                }
            ]

        def get_top_pinned_data(self):
            return [{
                'column_c' : 'value for C column',
                'column_d' : 'value for D column'
            }]


.. note:: Sorting and pagination for pinned rows not working.

Value for cell in pinned row will be shown only when **key** in object has the same name as column.
You can decide which columns for pinned rows will visible or not.
If you want show value for only one column, use only one column name as key.
Non existing keys won't be shown in pinned rows.


.. warning:: Pinned rows not exist in ``table.rows``. If table has some pinned rows and
   one normal row then length of ``table.rows`` is 1.


.. _pinned_row_attributes:

Attributes for pinned rows
~~~~~~~~~~~~~~~~~~~~~~~~~~

If you want to override HTML attributes for pinned rows you should use: ``pinned_row_attrs``.
Pinned row attributes can be specified using a `dict` defining the HTML attributes for
the ``<tr>`` element on each row. See more: :ref:`row-attributes`.

.. note:: By default pinned rows have ``pinned-row`` css class.

    .. sourcecode:: django

        <tr class="odd pinned-row" ...> [...] </tr>
        <tr class="even pinned-row" ...> [...] </tr>
