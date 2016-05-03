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

    Arguments:
        attrs (`dict`): Allows custom HTML attributes to be specified which will
            be added to the ``<table>`` tag of any table rendered via
            :meth:`.Table.as_html` or the
            :ref:`template-tags.render_table` template tag.

            This is typically used to enable a theme for a table (which is done
            by adding a CSS class to the ``<table>`` element). i.e.::

                class SimpleTable(tables.Table):
                    name = tables.Column()

                    class Meta:
                        attrs = {'class': 'paleblue'}

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
                        attrs = {'id': lambda: 'table_%d' % next(counter)}

            .. note::
                This functionality is also available via the ``attrs`` keyword
                argument to a table's constructor.

        row_attrs (`dict`): Allows custom HTML attributes to be specified which
            will be added to the ``<tr>`` tag of the rendered table.

            This can be used to add each record's primary key to each row::

                class PersonTable(tables.Table):
                    class Meta:
                        model = Person
                        row_attrs = {'data-id': lambda record: record.pk}

                # will result in
                '<tr data-id="1">...</tr>'

            .. versionadded:: 1.2.0

            .. note::

                This functionality is also available via the ``row_attrs`` keyword
                argument to a table's constructor.

        empty_text (str): Defines the text to display when the table has no rows.
            If the table is empty and ``bool(empty_text)`` is `True`, a row is
            displayed containing ``empty_text``. This is allows a message such as
            *There are currently no FOO.* to be displayed.

            .. note::

                This functionality is also available via the ``empty_text`` keyword
                argument to a table's constructor.

        show_header (bool): Defines whether the table header (``<thead>``)
            should be displayed or not.

            .. note::

                This functionality is also available via the ``show_header``
                keyword argument to a table's constructor.

        exclude (typle or str): Defines which columns should be excluded from
            the table. This is useful in subclasses to exclude columns in a
            parent::

                >>> class Person(tables.Table):
                ...     first_name = tables.Column()
                ...     last_name = tables.Column()
                ...
                >>> Person.base_columns
                {'first_name': <django_tables2.columns.Column object at 0x10046df10>,
                'last_name': <django_tables2.columns.Column object at 0x10046d8d0>}
                >>> class ForgetfulPerson(Person):
                ...     class Meta:
                ...         exclude = ('last_name', )
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

    fields (`tuple` or `str`): Used in conjunction with `~.Table.Meta.model`,
        specifies which fields should have columns in the table.

         - If `None`, all fields are used, otherwise only those named.

        Example::

            # models.py
            class Person(models.Model):
                first_name = models.CharField(max_length=200)
                last_name = models.CharField(max_length=200)

            # tables.py
            class PersonTable(tables.Table):
                class Meta:
                    model = Person
                    fields = ('first_name', )

    model (:class:`django.core.db.models.Model`): A model to inspect and
        automatically create corresponding columns.

        This option allows a Django model to be specified to cause the table to
        automatically generate columns that correspond to the fields in a
        model.

    order_by (tuple): The default ordering. e.g. ``('name', '-age')``.
        A hyphen `-` can be used to prefix a column name to indicate
        *descending* order.

        .. note::

            This functionality is also available via the ``order_by`` keyword
            argument to a table's constructor.

    sequence (iteralbe): The sequence of the table columns. This allows the
        default order of columns (the order they were defined in the Table) to
        be overridden.

        The special item ``'...'`` can be used as a placeholder that will be
        replaced with all the columns that weren't explicitly listed. This
        allows you to add columns to the front or back when using inheritance.

        Example::

            >>> class Person(tables.Table):
            ...     first_name = tables.Column()
            ...     last_name = tables.Column()
            ...
            ...     class Meta:
            ...         sequence = ('last_name', '...')
            ...
            >>> Person.base_columns.keys()
            ['last_name', 'first_name']

        The ``'...'`` item can be used at most once in the sequence value. If
        it's not used, every column *must* be explicitly included. e.g. in the
        above example, ``sequence = ('last_name', )`` would be **invalid**
        because neither ``'...'`` or ``'first_name'`` were included.

        .. note::

            This functionality is also available via the ``sequence`` keyword
            argument to a table's constructor.

    orderable (bool): Default value for column's *orderable* attribute.
        If the table and column don't specify a value, a column's ``orderable``
        value will fallback to this. This provides an easy mechanism to disable
        ordering on an entire table, without adding ``orderable=False`` to each
        column in a table.

        .. note::

            This functionality is also available via the ``orderable`` keyword
            argument to a table's constructor.

    template (str): The default template to use when rendering the table.

        .. note::

            This functionality is also available via the *template* keyword
            argument to a table's constructor.


    localize (str or tuple): Specifies which fields should be localized in the
        table. Read :ref:`localization-control` for more information.

    unlocalize (str or tuple): Specifies which fields should be unlocalized in
        the table. Read :ref:`localization-control` for more information.


`.Column`
---------

.. autoclass:: django_tables2.columns.Column


`.BooleanColumn`
----------------

.. autoclass:: django_tables2.columns.BooleanColumn


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

`.RelatedLinkColumn`
--------------------

.. autoclass:: django_tables2.columns.RelatedLinkColumn
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
