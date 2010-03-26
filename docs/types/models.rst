----------
ModelTable
----------

This table type is based on a Django model. It will use the Model's data,
and, like a ``ModelForm``, can automatically generate it's columns based
on the mode fields.

.. code-block:: python

    class CountryTable(tables.ModelTable):
        id = tables.Column(sortable=False, visible=False)
        class Meta:
            model = Country
            exclude = ['clicks']

In this example, the table will have one column for each model field,
with the exception of ``clicks``, which is excluded. The column for ``id``
is overwritten to both hide it by default and deny it sort capability.

When instantiating a ``ModelTable``, you usually pass it a queryset to
provide the table data:

.. code-block:: python

    qs = Country.objects.filter(continent="europe")
    countries = CountryTable(qs)

However, you can also just do:

.. code-block:: python

    countries = CountryTable()

and all rows exposed by the default manager of the model the table is based
on will be used.

If you are using model inheritance, then the following also works:

.. code-block:: python

    countries = CountryTable(CountrySubclass)

Note that while you can pass any model, it really only makes sense if the
model also provides fields for the columns you have defined.

If you just want to use a ``ModelTable``, but without auto-generated
columns, you do not have to list all model fields in the ``exclude``
``Meta`` option. Instead, simply don't specify a model.


Custom Columns
~~~~~~~~~~~~~~

You an add custom columns to your ModelTable that are not based on actual
model fields:

.. code-block:: python

    class CountryTable(tables.ModelTable):
        custom = tables.Column(default="foo")
        class Meta:
            model = Country

Just make sure your model objects do provide an attribute with that name.
Functions are also supported, so ``Country.custom`` could be a callable.


Spanning relationships
~~~~~~~~~~~~~~~~~~~~~~

Let's assume you have a ``Country`` model, with a ``ForeignKey`` ``capital``
pointing to the ``City`` model. While displaying a list of countries,
you might want want to link to the capital's geographic location, which is
stored in ``City.geo`` as a ``(lat, long)`` tuple, on, say, a Google Map.

``ModelTable`` supports the relationship spanning syntax of Django's
database API:

.. code-block:: python

    class CountryTable(tables.ModelTable):
        city__geo = tables.Column(name="geo")

This will add a column named "geo", based on the field by the same name
from the "city" relationship. Note that the name used to define the column
is what will be used to access the data, while the name-overwrite passed to
the column constructor just defines a prettier name for us to work with.
This is to be consistent with auto-generated columns based on model fields,
where the field/column name naturally equals the source name.

However, to make table defintions more visually appealing and easier to
read, an alternative syntax is supported: setting the column ``data``
property to the appropriate string.

.. code-block:: python

    class CountryTable(tables.ModelTable):
        geo = tables.Column(data='city__geo')

Note that you don't need to define a relationship's fields as separate
columns if you already have a column for the relationship itself, i.e.:

.. code-block:: python

    class CountryTable(tables.ModelTable):
        city = tables.Column()

    for country in countries.rows:
        print country.city.id
        print country.city.geo
        print country.city.founder.name


``ModelTable`` Specialties
~~~~~~~~~~~~~~~~~~~~~~~~~~

``ModelTable`` currently has some restrictions with respect to ordering:

* Custom columns not based on a model field do not support ordering,
  regardless of the ``sortable`` property (it is ignored).

* A ``ModelTable`` column's ``default`` or ``data`` value does not affect
  ordering. This differs from the non-model table behaviour.

If a column is mapped to a method on the model, that method will be called
without arguments. This behavior differs from memory tables, where a
row object will be passed.

If you are using callables (e.g. for the ``default`` or ``data`` column
options), they will generally be run when a row is accessed, and
possible repeatedly when accessed more than once. This behavior differs from
memory tables, where they would be called once, when the table is
generated.