API Reference
=============

`.Accessor` (`.A`)
------------------

.. autoclass:: django_tables2.utils.Accessor


`.RequestConfig`
----------------

.. autoclass:: django_tables2.config.RequestConfig


`.Table`
--------

.. autoclass:: django_tables2.tables.Table
    :members: paginate, as_html


`.Table.Meta`
-------------

.. class:: Table.Meta

    Provides a way to define *global* settings for table, as opposed to
    defining them for each instance.

    .. attribute:: attrs

        Allows custom HTML attributes to be specified which will be added to
        the ``<table>`` tag of any table rendered via
        :meth:`.Table.as_html` or the
        :ref:`template-tags.render_table` template tag.

        :type: `dict`
        :default: ``{}``

        This is typically used to enable a theme for a table (which is done by
        adding a CSS class to the ``<table>`` element). i.e.::

            class SimpleTable(tables.Table):
                name = tables.Column()

                class Meta:
                    attrs = {"class": "paleblue"}

        .. versionadded:: 0.15.0

        It's possible to use callables to create *dynamic* values. A few caveats:

        - It's not supported for ``dict`` keys, i.e. only values.
        - All values will be resolved on table instantiation.

        Consider this example where a unique ``id`` is given to each instance
        of the table::

            import itertools
            counter = itertools.count()

            class UniqueIdTable(tables.Table):
                name = tables.Column()

                class Meta:
                    attrs = {"id": lambda: "table_%d" % next(counter)}

        .. note::

            This functionality is also available via the ``attrs`` keyword
            argument to a table's constructor.

    .. attribute:: empty_text

        Defines the text to display when the table has no rows.

        :type: `unicode`
        :default: `None`

        If the table is empty and ``bool(empty_text)`` is `True`, a row is
        displayed containing ``empty_text``. This is allows a message such as
        *There are currently no FOO.* to be displayed.

        .. note::

            This functionality is also available via the ``empty_text`` keyword
            argument to a table's constructor.

    .. attribute:: exclude

        Defines which columns should be excluded from the table. This is useful
        in subclasses to exclude columns in a parent.

        :type: tuple of `unicode`
        :default: ``()``

        Example::

            >>> class Person(tables.Table):
            ...     first_name = tables.Column()
            ...     last_name = tables.Column()
            ...
            >>> Person.base_columns
            {'first_name': <django_tables2.columns.Column object at 0x10046df10>,
            'last_name': <django_tables2.columns.Column object at 0x10046d8d0>}
            >>> class ForgetfulPerson(Person):
            ...     class Meta:
            ...         exclude = ("last_name", )
            ...
            >>> ForgetfulPerson.base_columns
            {'first_name': <django_tables2.columns.Column object at 0x10046df10>}

        .. note::

            This functionality is also available via the ``exclude`` keyword
            argument to a table's constructor.

            However, unlike some of the other `.Table.Meta` options, providing the
            ``exclude`` keyword to a table's constructor **won't override** the
            `.Meta.exclude`. Instead, it will be effectively be *added*
            to it. i.e. you can't use the constructor's ``exclude`` argument to
            *undo* an exclusion.

    .. attribute:: fields

        Used in conjunction with `~.Table.Meta.model`, specifies which fields
        should have columns in the table.

        :type: tuple of `unicode` or `None`
        :default: `None`

        If `None`, all fields are used, otherwise only those named.

        Example::

            # models.py
            class Person(models.Model):
                first_name = models.CharField(max_length=200)
                last_name = models.CharField(max_length=200)

            # tables.py
            class PersonTable(tables.Table):
                class Meta:
                    model = Person
                    fields = ("first_name", )

    .. attribute:: model

        A model to inspect and automatically create corresponding columns.

        :type: Django model
        :default: `None`

        This option allows a Django model to be specified to cause the table to
        automatically generate columns that correspond to the fields in a
        model.

    .. attribute:: order_by

        The default ordering. e.g. ``('name', '-age')``. A hyphen ``-`` can be
        used to prefix a column name to indicate *descending* order.

        :type: `tuple`
        :default: ``()``

        .. note::

            This functionality is also available via the ``order_by`` keyword
            argument to a table's constructor.

    .. attribute:: sequence

        The sequence of the table columns. This allows the default order of
        columns (the order they were defined in the Table) to be overridden.

        :type: any iterable (e.g. `tuple` or `list`)
        :default: ``()``

        The special item ``"..."`` can be used as a placeholder that will be
        replaced with all the columns that weren't explicitly listed. This
        allows you to add columns to the front or back when using inheritence.

        Example::

            >>> class Person(tables.Table):
            ...     first_name = tables.Column()
            ...     last_name = tables.Column()
            ...
            ...     class Meta:
            ...         sequence = ("last_name", "...")
            ...
            >>> Person.base_columns.keys()
            ['last_name', 'first_name']

        The ``"..."`` item can be used at most once in the sequence value. If
        it's not used, every column *must* be explicitly included. e.g. in the
        above example, ``sequence = ("last_name", )`` would be **invalid**
        because neither ``"..."`` or ``"first_name"`` were included.

        .. note::

            This functionality is also available via the ``sequence`` keyword
            argument to a table's constructor.

    .. attribute:: orderable

        Default value for column's *orderable* attribute.

        :type: `bool`
        :default: `True`

        If the table and column don't specify a value, a column's
        ``orderable`` value will fallback to this. object specify. This
        provides an easy mechanism to disable ordering on an entire table,
        without adding ``orderable=False`` to each column in a table.

        .. note::

            This functionality is also available via the ``orderable`` keyword
            argument to a table's constructor.

    .. attribute:: template

        The default template to use when rendering the table.

        :type: `unicode`
        :default: ``"django_tables2/table.html"``

        .. note::

            This functionality is also available via the *template* keyword
            argument to a table's constructor.


    .. attribute:: localize

        Specifies which fields should be localized in the table.
        Read :ref:`localization-control` for more information.

        :type: tuple of `unicode`
        :default: empty tuple


    .. attribute:: unlocalize

        Specifies which fields should be unlocalized in the table.
        Read :ref:`localization-control` for more information.

        :type: tuple of `unicode`
        :default: empty tuple


`.BooleanColumn`
----------------

.. autoclass:: django_tables2.columns.BooleanColumn


`.Column`
---------

.. autoclass:: django_tables2.columns.Column


`.CheckBoxColumn`
-----------------

.. autoclass:: django_tables2.columns.CheckBoxColumn
    :members:


`.DateColumn`
-------------

.. autoclass:: django_tables2.columns.DateColumn
    :members:


`.DateTimeColumn`
-----------------

.. autoclass:: django_tables2.columns.DateTimeColumn
    :members:


`.EmailColumn`
--------------

.. autoclass:: django_tables2.columns.EmailColumn
    :members:


`.FileColumn`
-------------

.. autoclass:: django_tables2.columns.FileColumn
    :members:


`.LinkColumn`
-------------

.. autoclass:: django_tables2.columns.LinkColumn
    :members:


`.TemplateColumn`
-----------------

.. autoclass:: django_tables2.columns.TemplateColumn
    :members:


`.URLColumn`
------------

.. autoclass:: django_tables2.columns.URLColumn
    :members:


See :doc:`internal` for internal classes.
