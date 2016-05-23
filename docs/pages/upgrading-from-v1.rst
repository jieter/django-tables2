Upgrading from django-tables Version 1
======================================

- Change your ``INSTALLLED_APPS`` entry from ``'django_tables.app'`` to
  ``'django_tables2'``.

- Change all your import references from ``django_tables`` to
  ``django_tables2``.

- Replace all references to the old ``MemoryTable`` and ``ModelTable``
  classes with simply ``Table``.

- In your templates, load the ``django_tables2`` template library;
  ``{% load django_tables2 %}`` instead of ``{% load tables %}``.

- A table object is no longer iterable; rather than ``for row in table``,
  instead you now do explicitly: ``for row in table.rows``.

- If you were using ``row.data`` to access a row's underlying data,
  replace it with ``row.record`` instead.

- When declaring columns, replace the use of::

    name_in_dataset = tables.Column(name='wanted_column_name')

  with::

    wanted_column_name = tables.Column(accessor='name_in_dataset')

- When declaring columns, replace the use of::

     column_to_override = tables.Column(name='wanted_column_name', data='name_in_dataset')

  with::

     wanted_column_name = tables.Column(accessor='name_in_dataset')

  and exclude ``column_to_override`` via the table meta data.

- When generating the link to order the column, instead of:

  .. sourcecode:: django

      {% set_url_param sort=column.name_toggled %}

  use:

  .. sourcecode:: django

      {% querystring table.order_by_field=column.order_by_alias.next %}

- Replace:

  .. sourcecode:: django

      {{ column.is_ordered_reverse }} and {{ column.is_ordered_straight }}

  with:

  .. sourcecode:: django

      {{ column.order_by.is_descending }} and {{ column.order_by.is_ascending }}
