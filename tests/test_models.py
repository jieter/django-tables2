"""Test ModelTable specific functionality.

Sets up a temporary Django project using a memory SQLite database.
"""

from django.conf import settings

def setup_module(module):
    settings.configure(**{
        'DATABASE_ENGINE': 'sqlite3',
        'DATABASE_NAME': ':memory:',
    })

    from django.db import models

    class City(models.Model):
        name = models.TextField()
        population = models.IntegerField()
    module.City = City

    class Country(models.Model):
        name = models.TextField()
        population = models.IntegerField()
        capital = models.ForeignKey(City)
        tld = models.TextField(verbose_name='Domain Extension', max_length=2)
    module.Country = Country


def test_nothing():
    pass

import django_tables as tables

def test_declaration():
    """Test declaration, declared columns and default model field columns.
    """

    class CountryTable(tables.ModelTable):
        class Meta:
            model = Country

    assert len(CountryTable.base_columns) == 5
    assert 'name' in CountryTable.base_columns
    assert not hasattr(CountryTable, 'name')

    # Override one model column, add another custom one, exclude one
    class CountryTable(tables.ModelTable):
        capital = tables.TextColumn(verbose_name='Name of capital')
        projected = tables.Column(verbose_name="Projected Population")
        class Meta:
            model = Country
            exclude = ['tld']

    assert len(CountryTable.base_columns) == 5
    assert 'projected' in CountryTable.base_columns
    assert 'capital' in CountryTable.base_columns
    assert not 'tld' in CountryTable.base_columns

    # Inheritance (with a different model) + field restrictions
    class CityTable(CountryTable):
        class Meta:
            model = City
            columns = ['id', 'name']
            exclude = ['capital']

    print CityTable.base_columns
    assert len(CityTable.base_columns) == 4
    assert 'id' in CityTable.base_columns
    assert 'name' in CityTable.base_columns
    assert 'projected' in CityTable.base_columns # declared in parent
    assert not 'population' in CityTable.base_columns  # not in Meta:columns
    assert 'capital' in CityTable.base_columns  # in exclude, but only works on model fields (is that the right behaviour?)