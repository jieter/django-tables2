"""Test template specific functionality.

Make sure tables expose their functionality to templates right. This
generally about testing "out"-functionality of the tables, whether
via templates or otherwise. Whether a test belongs here or, say, in
``test_basic``, is not always a clear-cut decision.
"""

from py.test import raises
from django.template import Template, Context, add_to_builtins
from django.http import HttpRequest
import django_tables as tables

def test_order_by():
    class BookTable(tables.Table):
        id = tables.Column()
        name = tables.Column()
    books = BookTable([
        {'id': 1, 'name': 'Foo: Bar'},
    ])

    # cast to a string we get a value ready to be passed to the querystring
    books.order_by = ('name',)
    assert str(books.order_by) == 'name'
    books.order_by = ('name', '-id')
    assert str(books.order_by) == 'name,-id'

def test_columns_and_rows():
    class CountryTable(tables.Table):
        name = tables.TextColumn()
        capital = tables.TextColumn(sortable=False)
        population = tables.NumberColumn(verbose_name="Population Size")
        currency = tables.NumberColumn(visible=False, inaccessible=True)
        tld = tables.TextColumn(visible=False, verbose_name="Domain")
        calling_code = tables.NumberColumn(name="cc", verbose_name="Phone Ext.")

    countries = CountryTable(
        [{'name': 'Germany', 'capital': 'Berlin', 'population': 83, 'currency': 'Euro (€)', 'tld': 'de', 'cc': 49},
         {'name': 'France', 'population': 64, 'currency': 'Euro (€)', 'tld': 'fr', 'cc': 33},
         {'name': 'Netherlands', 'capital': 'Amsterdam', 'cc': '31'},
         {'name': 'Austria', 'cc': 43, 'currency': 'Euro (€)', 'population': 8}])

    assert len(list(countries.columns)) == 4
    assert len(list(countries.rows)) == len(list(countries)) == 4

    # column name override, hidden columns
    assert [c.name for c in countries.columns] == ['name', 'capital', 'population', 'cc']
    # verbose_name, and fallback to field name
    assert [unicode(c) for c in countries.columns] == ['Name', 'Capital', 'Population Size', 'Phone Ext.']

    # data yielded by each row matches the defined columns
    for row in countries.rows:
        assert len(list(row)) == len(list(countries.columns))

    # we can access each column and row by name...
    assert countries.columns['population'].column.verbose_name == "Population Size"
    assert countries.columns['cc'].column.verbose_name == "Phone Ext."
    # ...even invisible ones
    assert countries.columns['tld'].column.verbose_name == "Domain"
    # ...and even inaccessible ones (but accessible to the coder)
    assert countries.columns['currency'].column == countries.base_columns['currency']
    # this also works for rows
    for row in countries:
        row['tld'], row['cc'], row['population']

    # certain data is available on columns
    assert countries.columns['currency'].sortable == True
    assert countries.columns['capital'].sortable == False
    assert countries.columns['name'].visible == True
    assert countries.columns['tld'].visible == False

def test_render():
    """For good measure, render some actual templates."""

    class CountryTable(tables.Table):
        name = tables.TextColumn()
        capital = tables.TextColumn()
        population = tables.NumberColumn(verbose_name="Population Size")
        currency = tables.NumberColumn(visible=False, inaccessible=True)
        tld = tables.TextColumn(visible=False, verbose_name="Domain")
        calling_code = tables.NumberColumn(name="cc", verbose_name="Phone Ext.")

    countries = CountryTable(
        [{'name': 'Germany', 'capital': 'Berlin', 'population': 83, 'currency': 'Euro (€)', 'tld': 'de', 'calling_code': 49},
         {'name': 'France', 'population': 64, 'currency': 'Euro (€)', 'tld': 'fr', 'calling_code': 33},
         {'name': 'Netherlands', 'capital': 'Amsterdam', 'calling_code': '31'},
         {'name': 'Austria', 'calling_code': 43, 'currency': 'Euro (€)', 'population': 8}])

    assert Template("{% for column in countries.columns %}{{ column }}/{{ column.name }} {% endfor %}").\
        render(Context({'countries': countries})) == \
        "Name/name Capital/capital Population Size/population Phone Ext./cc "

    assert Template("{% for row in countries %}{% for value in row %}{{ value }} {% endfor %}{% endfor %}").\
        render(Context({'countries': countries})) == \
        "Germany Berlin 83 49 France None 64 33 Netherlands Amsterdam None 31 Austria None 8 43 "

    print Template("{% for row in countries %}{% if countries.columns.name.visible %}{{ row.name }} {% endif %}{% if countries.columns.tld.visible %}{{ row.tld }} {% endif %}{% endfor %}").\
        render(Context({'countries': countries})) == \
        "Germany France Netherlands Austria"

def test_templatetags():
    add_to_builtins('django_tables.app.templatetags.tables')

    # [bug] set url param tag handles an order_by tuple with multiple columns
    class MyTable(tables.Table):
        f1 = tables.Column()
        f2 = tables.Column()
    t = Template('{% set_url_param x=table.order_by %}')
    table = MyTable([], order_by=('f1', 'f2'))
    assert t.render({'request': HttpRequest(), 'table': table}) == '?x=f1%2Cf2'
