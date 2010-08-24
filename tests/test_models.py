"""Test ModelTable specific functionality.

Sets up a temporary Django project using a memory SQLite database.
"""

from nose.tools import assert_raises, assert_equal
from django.conf import settings
from django.core.paginator import *
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
        population = models.IntegerField(null=True)
        class Meta:
            app_label = 'testapp'
    module.City = City

    class Country(models.Model):
        name = models.TextField()
        population = models.IntegerField()
        capital = models.ForeignKey(City, blank=True, null=True)
        tld = models.TextField(verbose_name='Domain Extension', max_length=2)
        system = models.TextField(blank=True, null=True)
        null = models.TextField(blank=True, null=True)   # tests expect this to be always null!
        null2 = models.TextField(blank=True, null=True)  #  - " -
        def example_domain(self):
            return 'example.%s' % self.tld
        class Meta:
            app_label = 'testapp'
    module.Country = Country

    # create the tables
    call_command('syncdb', verbosity=1, interactive=False)

    # create a couple of objects
    berlin=City(name="Berlin"); berlin.save()
    amsterdam=City(name="Amsterdam"); amsterdam.save()
    Country(name="Austria", tld="au", population=8, system="republic").save()
    Country(name="Germany", tld="de", population=81, capital=berlin).save()
    Country(name="France", tld="fr", population=64, system="republic").save()
    Country(name="Netherlands", tld="nl", population=16, system="monarchy", capital=amsterdam).save()


class TestDeclaration:
    """Test declaration, declared columns and default model field columns.
    """

    def test_autogen_basic(self):
        class CountryTable(tables.ModelTable):
            class Meta:
                model = Country

        assert len(CountryTable.base_columns) == 8
        assert 'name' in CountryTable.base_columns
        assert not hasattr(CountryTable, 'name')

        # Override one model column, add another custom one, exclude one
        class CountryTable(tables.ModelTable):
            capital = tables.TextColumn(verbose_name='Name of capital')
            projected = tables.Column(verbose_name="Projected Population")
            class Meta:
                model = Country
                exclude = ['tld']

        assert len(CountryTable.base_columns) == 8
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

    def test_columns_custom_order(self):
        """Using the columns meta option, you can also modify the ordering.
        """
        class CountryTable(tables.ModelTable):
            foo = tables.Column()
            class Meta:
                model = Country
                columns = ('system', 'population', 'foo', 'tld',)

        assert [c.name for c in CountryTable().columns] == ['system', 'population', 'foo', 'tld']


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
            # [bug] access to data that might be available, but does not
            # have a corresponding column is denied.
            assert_raises(Exception, "r['id']")
            # missing data is available with default values
            assert 'null' in r
            assert r['null'] == "foo"   # note: different from prev. line!
            # if everything else fails (no default), we get None back
            assert r['null2'] is None

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
        null2 = tables.Column()
        tld = tables.Column(name="domain")
    countries = CountryTable(Country)
    test_country_table(countries)


def test_invalid_accessor():
    """Test that a column being backed by a non-existent model property
    is handled correctly.

    Regression-Test: There used to be a NameError here.
    """
    class CountryTable(tables.ModelTable):
        name = tables.Column(data='something-i-made-up')
    countries = CountryTable(Country)
    assert_raises(ValueError, countries[0].__getitem__, 'name')


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
        population = tables.Column()
        system = tables.Column(default="republic")
        custom1 = tables.Column()
        custom2 = tables.Column(sortable=True)
        class Meta:
            model = Country
    countries = CountryTable()

    def test_order(order, result, table=countries):
        table.order_by = order
        assert [r['id'] for r in table.rows] == result

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
    # using a simple string (for convinience as well as querystring passing)
    test_order('-population', [2,3,4,1])
    test_order('system,-population', [2,4,3,1])

    # test column with a default ``direction`` set to descending
    class CityTable(tables.ModelTable):
        name = tables.Column(direction='desc')
        class Meta:
            model = City
    cities = CityTable()
    test_order('name', [1,2], table=cities)   # Berlin to Amsterdam
    test_order('-name', [2,1], table=cities)  # Amsterdam to Berlin

    # test invalid order instructions...
    countries.order_by = 'invalid_field,population'
    assert countries.order_by == ('population',)
    # ...in case of ModelTables, this primarily means that only
    # model-based colunns are currently sortable at all.
    countries.order_by = ('custom1', 'custom2')
    assert countries.order_by == ()

def test_default_sort():
    class SortedCountryTable(tables.ModelTable):
        class Meta:
            model = Country
            order_by = '-name'

    # the order_by option is provided by TableOptions
    assert_equal('-name', SortedCountryTable()._meta.order_by)

    # the default order can be inherited from the table
    assert_equal(('-name',), SortedCountryTable().order_by)
    assert_equal(4, SortedCountryTable().rows[0]['id'])

    # and explicitly set (or reset) via __init__
    assert_equal(2, SortedCountryTable(order_by='system').rows[0]['id'])
    assert_equal(1, SortedCountryTable(order_by=None).rows[0]['id'])

def test_callable():
    """Some of the callable code is reimplemented for modeltables, so
    test some specifics again.
    """

    class CountryTable(tables.ModelTable):
        null = tables.Column(default=lambda s: s['example_domain'])
        example_domain = tables.Column()
        class Meta:
            model = Country
    countries = CountryTable(Country)

    # model method is called
    assert [row['example_domain'] for row in countries] == \
                    ['example.'+row['tld'] for row in countries]

    # column default method is called
    assert [row['example_domain'] for row in countries] == \
                    [row['null'] for row in countries]


def test_relationships():
    """Test relationship spanning."""

    class CountryTable(tables.ModelTable):
        # add relationship spanning columns (using different approaches)
        capital_name = tables.Column(data='capital__name')
        capital__population = tables.Column(name="capital_population")
        invalid = tables.Column(data="capital__invalid")
        class Meta:
            model = Country
    countries = CountryTable(Country.objects.select_related('capital'))

    # ordering and field access works
    countries.order_by = 'capital_name'
    assert [row['capital_name'] for row in countries.rows] == \
        [None, None, 'Amsterdam', 'Berlin']

    countries.order_by = 'capital_population'
    assert [row['capital_population'] for row in countries.rows] == \
        [None, None, None, None]

    # ordering by a column with an invalid relationship fails silently
    countries.order_by = 'invalid'
    assert countries.order_by == ()


def test_pagination():
    """Pretty much the same as static table pagination, but make sure we
    provide the capability, at least for paginators that use it, to not
    have the complete queryset loaded (by use of a count() query).

    Note: This test changes the available cities, make sure it is last,
    or that tests that follow are written appropriately.
    """
    from django.db import connection

    class CityTable(tables.ModelTable):
        class Meta:
            model = City
            columns = ['name']
    cities = CityTable()

    # add some sample data
    City.objects.all().delete()
    for i in range(1,101):
        City.objects.create(name="City %d"%i)

    # for query logging
    settings.DEBUG = True

    # external paginator
    start_querycount = len(connection.queries)
    paginator = Paginator(cities.rows, 10)
    assert paginator.num_pages == 10
    page = paginator.page(1)
    assert len(page.object_list) == 10
    assert page.has_previous() == False
    assert page.has_next() == True
    # Make sure the queryset is not loaded completely - there must be two
    # queries, one a count(). This check is far from foolproof...
    assert len(connection.queries)-start_querycount == 2

    # using a queryset paginator is possible as well (although unnecessary)
    paginator = QuerySetPaginator(cities.rows, 10)
    assert paginator.num_pages == 10

    # integrated paginator
    start_querycount = len(connection.queries)
    cities.paginate(Paginator, 10, page=1)
    # rows is now paginated
    assert len(list(cities.rows.page())) == 10
    assert len(list(cities.rows.all())) == 100
    # new attributes
    assert cities.paginator.num_pages == 10
    assert cities.page.has_previous() == False
    assert cities.page.has_next() == True
    assert len(connection.queries)-start_querycount == 2

    # reset
    settings.DEBUG = False