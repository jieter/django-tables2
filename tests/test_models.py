"""Test ModelTable specific functionality.

Sets up a temporary Django project using a memory SQLite database.
"""

from django.conf import settings
import django_tables as tables

def setup_module(module):
    settings.configure(**{
        'DATABASE_ENGINE': 'sqlite3',
        'DATABASE_NAME': ':memory:',
        'INSTALLED_APPS': ('tests.testapp',)
    })

    from django.db import models
    from django.core.management import call_command

    class City(models.Model):
        name = models.TextField()
        population = models.IntegerField()
        class Meta:
            app_label = 'testapp'
    module.City = City

    class Country(models.Model):
        name = models.TextField()
        population = models.IntegerField()
        capital = models.ForeignKey(City, blank=True, null=True)
        tld = models.TextField(verbose_name='Domain Extension', max_length=2)
        system = models.TextField(blank=True, null=True)
        null = models.TextField(blank=True, null=True)  # tests expect this to be always null!
        class Meta:
            app_label = 'testapp'
    module.Country = Country

    # create the tables
    call_command('syncdb', verbosity=1, interactive=False)

    # create a couple of objects
    Country(name="Austria", tld="au", population=8, system="republic").save()
    Country(name="Germany", tld="de", population=81).save()
    Country(name="France", tld="fr", population=64, system="republic").save()
    Country(name="Netherlands", tld="nl", population=16, system="monarchy").save()

def test_declaration():
    """Test declaration, declared columns and default model field columns.
    """

    class CountryTable(tables.ModelTable):
        class Meta:
            model = Country

    assert len(CountryTable.base_columns) == 7
    assert 'name' in CountryTable.base_columns
    assert not hasattr(CountryTable, 'name')

    # Override one model column, add another custom one, exclude one
    class CountryTable(tables.ModelTable):
        capital = tables.TextColumn(verbose_name='Name of capital')
        projected = tables.Column(verbose_name="Projected Population")
        class Meta:
            model = Country
            exclude = ['tld']

    assert len(CountryTable.base_columns) == 7
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

def test_basic():
    """Some tests here are copied from ``test_basic.py`` but need to be
    rerun with a ModelTable, as the implementation is different."""

    class CountryTable(tables.ModelTable):
        null = tables.Column(default="foo")
        tld = tables.Column(name="domain")
        class Meta:
            model = Country
            exclude = ('id',)
    countries = CountryTable()

    def test_country_table(table):
        for r in table.rows:
            # "normal" fields exist
            assert 'name' in r
            # unknown fields are removed/not accessible
            assert not 'does-not-exist' in r
            # ...so are excluded fields
            assert not 'id' in r
            # missing data is available with default values
            assert 'null' in r
            assert r['null'] == "foo"   # note: different from prev. line!

            # all that still works when name overrides are used
            assert not 'tld' in r
            assert 'domain' in r
            assert len(r['domain']) == 2   # valid country tld
    test_country_table(countries)

    # repeat the avove tests with a table that is not associated with a
    # model, and all columns being created manually.
    class CountryTable(tables.ModelTable):
        name = tables.Column()
        population = tables.Column()
        capital = tables.Column()
        system = tables.Column()
        null = tables.Column(default="foo")
        tld = tables.Column(name="domain")
    countries = CountryTable(Country)
    test_country_table(countries)

def test_caches():
    """Make sure the caches work for model tables as well (parts are
    reimplemented).
    """
    class CountryTable(tables.ModelTable):
        class Meta:
            model = Country
            exclude = ('id',)
    countries = CountryTable()

    assert id(list(countries.columns)[0]) == id(list(countries.columns)[0])
    # TODO: row cache currently not used
    #assert id(list(countries.rows)[0]) == id(list(countries.rows)[0])

    # test that caches are reset after an update()
    old_column_cache = id(list(countries.columns)[0])
    old_row_cache = id(list(countries.rows)[0])
    countries.update()
    assert id(list(countries.columns)[0]) != old_column_cache
    assert id(list(countries.rows)[0]) != old_row_cache

def test_sort():
    class CountryTable(tables.ModelTable):
        tld = tables.Column(name="domain")
        system = tables.Column(default="republic")
        custom1 = tables.Column()
        custom2 = tables.Column(sortable=True)
        class Meta:
            model = Country
    countries = CountryTable()

    def test_order(order, result):
        countries.order_by = order
        assert [r['id'] for r in countries.rows] == result

    # test various orderings
    test_order(('population',), [1,4,3,2])
    test_order(('-population',), [2,3,4,1])
    test_order(('name',), [1,3,2,4])
    # test sorting with a "rewritten" column name
    countries.order_by = 'domain,tld'      # "tld" would be invalid...
    countries.order_by == ('domain',)      # ...and is therefore removed
    test_order(('-domain',), [4,3,2,1])
    # test multiple order instructions; note: one row is missing a "system"
    # value, but has a default set; however, that has no effect on sorting.
    test_order(('system', '-population'), [2,4,3,1])
    # using a simple string (for convinience as well as querystring passing
    test_order('-population', [2,3,4,1])
    test_order('system,-population', [2,4,3,1])

    # test invalid order instructions...
    countries.order_by = 'invalid_field,population'
    assert countries.order_by == ('population',)
    # ...in case of ModelTables, this primarily means that only
    # model-based colunns are currently sortable at all.
    countries.order_by = ('custom1', 'custom2')
    assert countries.order_by == ()

def test_pagination():
    pass

# TODO: pagination
# TODO: support function column sources both for modeltables (methods on model) and static tables (functions in dict)
# TODO: support relationship spanning columns (we could generate select_related() automatically)