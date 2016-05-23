Alternative column ordering
===========================

When using queryset data, one might want to show a computed value which is not
in the database. In this case, attempting to order the column will cause an
exception::

    # models.py
    class Person(models.Model):
        first_name = models.CharField(max_length=200)
        family_name = models.CharField(max_length=200)

        @property
        def name(self):
            return '{} {}'.format(self.first_name, self.family_name)

    # tables.py
    class PersonTable(tables.Table):
        name = tables.Column()

::

    >>> table = PersonTable(Person.objects.all())
    >>> table.order_by = 'name'
    >>>
    >>> # will result in:
    FieldError: Cannot resolve keyword 'name' into field. Choices are: first_name, family_name

To prevent this, django-tables2 allows two ways to specify custom ordering:
accessors and :meth:`~.order_FOO` methods.

.. _order-by-accessors:

Ordering by accessors
---------------------

You can supply an ``order_by`` argument containing a name or a tuple of the
names of the columns the database should use to sort it::

    class PersonTable(tables.Table):
        name = tables.Column(order_by=('first_name', 'family_name'))

`~.Accessor` syntax can be used as well, as long as they point to a model field.

If ordering does not make sense for a particular column, it can be disabled via
the ``orderable`` argument::

    class SimpleTable(tables.Table):
        name = tables.Column()
        actions = tables.Column(orderable=False)


.. _table.order_foo:

:meth:`table.order_FOO` methods
--------------------------------

Another solution for alternative ordering is being able to chain functions on to
the original queryset. This method allows more complex functionality giving the
ability to use all of Django's QuerySet API.

Adding a `Table.order_FOO` method (where `FOO` is the name of the column),
gives you the ability to chain to, or modify, the original queryset when that
column is selected to be ordered.

The method takes two arguments: `queryset`, and `is_descending`. The return
must be a tuple of two elements. The first being the queryset and the second
being a boolean; note that modified queryset will only be used if the boolean is
`True`.

For example, let's say instead of ordering alphabetically, ordering by
amount of characters in the first_name is desired.
The implementation would look like this:
::

    # tables.py
    from django.db.models.functions import Length

    class PersonTable(tables.Table):
        name = tables.Column()

        def order_name(self, queryset, is_descending):
            queryset = queryset.annotate(
                length=Length('first_name')
            ).order_by(('-' if is_descending else '') + 'length')
            return (queryset, True)



As another example, presume the situation calls for being able to order by a
mathematical expression. In this scenario, the table needs to be able to be
ordered by the sum of both the shirts and the pants. The custom column will
have its value rendered using :ref:`table.render_FOO`.

This can be achieved like this::

    # models.py
    class Person(models.Model):
        first_name = models.CharField(max_length=200)
        family_name = models.CharField(max_length=200)
        shirts = models.IntegerField()
        pants = models.IntegerField()


    # tables.py
    from django.db.models import F

    class PersonTable(tables.Table):
        clothing = tables.Column()

        class Meta:
            model = Person

        def render_clothing(self, record):
            return str(record.shirts + record.pants)

        def order_clothing(self, queryset, is_descending):
            queryset = queryset.annotate(
                amount=F('shirts') + F('pants')
            ).order_by(('-' if is_descending else '') + 'amount')
            return (queryset, True)
