.. _order-by-accessors:

Specifying alternative ordering for a column
============================================

When using queryset data, it's possible for a column to present a computed
value that doesn't correspond to a column in the database. In this situation
attempting to order the column will cause a database exception.

Example::

    # models.py
    class Person(models.Model):
        first_name = models.CharField(max_length=200)
        family_name = models.CharField(max_length=200)

        @property
        def name(self):
            return u"%s %s" % (self.first_name, self.family_name)

    # tables.py
    class PersonTable(tables.Table):
        name = tables.Column()

::

    >>> table = PersonTable(Person.objects.all())
    >>> table.order_by = "name"
    >>> table.as_html()
    ...
    FieldError: Cannot resolve keyword u'name' into field. Choices are: first_name, family_name

The solution is to declare which fields should be used when ordering on via the
``order_by`` argument::

    # tables.py
    class PersonTable(tables.Table):
        name = tables.Column(order_by=("first_name", "family_name"))

Accessor syntax can be used for the values, but they must terminate on a model
field.

If ordering doesn't make sense for a particular column, it can be disabled via
the ``orderable`` argument::

    class SimpleTable(tables.Table):
        name = tables.Column()
        actions = tables.Column(orderable=False)
