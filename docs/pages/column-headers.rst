.. _column-headers:

Customising column headings
===========================

The header cell for each column comes from `~.Column.header`. By default this
method returns `~.Column.verbose_name`, falling back to the titlised attribute
name of the column in the table class.

When using queryset data and a verbose name hasn't been explicitly
defined for a column, the corresponding model field's verbose name will be
used.

Consider the following:

    >>> class Person(models.Model):
    ...     first_name = models.CharField(verbose_name='model verbose name', max_length=200)
    ...     last_name = models.CharField(max_length=200)
    ...     region = models.ForeignKey('Region')
    ...
    >>> class Region(models.Model):
    ...     name = models.CharField(max_length=200)
    ...
    >>> class PersonTable(tables.Table):
    ...     first_name = tables.Column()
    ...     ln = tables.Column(accessor='last_name')
    ...     region_name = tables.Column(accessor='region.name')
    ...
    >>> table = PersonTable(Person.objects.all())
    >>> table.columns['first_name'].header
    u'Model Verbose Name'
    >>> table.columns['ln'].header
    u'Last Name'
    >>> table.columns['region_name'].header
    u'Name'

As you can see in the last example (region name), the results are not always
desirable when an accessor is used to cross relationships. To get around this
be careful to define `.Column.verbose_name`.
