.. _localization-control:

Controlling localization
========================

Django-tables2 allows you to define which column of a table should or should not
be localized. For example you may want to use this feature in following use cases:

* You want to format some columns representing for example numeric values in the given locales
  even if you don't enable `USE_L10N` in your settings file.

* You don't want to format primary key values in your table
  even if you enabled `USE_L10N` in your settings file.

This control is done by using two filter functions in Django's `l10n` library
named `localize` and `unlocalize`. Check out Django docs about
`localization <https://docs.djangoproject.com/en/stable/topics/i18n/formatting/>` for more information about them.

There are two ways of controlling localization in your columns.

First one is setting the `~.Column.localize` attribute in your column definition
to `True` or `False`. Like so::

     class PersonTable(tables.Table):
        id = tables.Column(name='id', accessor='pk', localize=False)
        class Meta:
            model = Person


.. note::
    The default value of the `localize` attribute is `None` which means the formatting
    of columns is dependant from the `USE_L10N` setting.

The second way is to define a `~.Table.Meta.localize` and/or `~.Table.Meta.unlocalize`
tuples in your tables Meta class (jutst like with `~.Table.Meta.fields`
or `~.Table.Meta.exclude`). You can do this like so::

     class PersonTable(tables.Table):
        id = tables.Column(accessor='pk')
        value = tables.Column(accessor='some_numerical_field')
        class Meta:
            model = Person
            unlocalize = ('id', )
            localize = ('value', )

If you define the same column in both `localize` and `unlocalize` then the value
of this column will be 'unlocalized' which means that `unlocalize` has higher precedence.
