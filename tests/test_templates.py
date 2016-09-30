# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.template import Context, Template
from django.test import TransactionTestCase
from django.utils.translation import override as translation_override
from django.utils.translation import ugettext_lazy

import django_tables2 as tables
from django_tables2.config import RequestConfig

from .app.models import Person
from .utils import build_request, parse


class CountryTable(tables.Table):
    name = tables.Column()
    capital = tables.Column(orderable=False,
                            verbose_name=ugettext_lazy("Capital"))
    population = tables.Column(verbose_name='Population Size')
    currency = tables.Column(visible=False)
    tld = tables.Column(visible=False, verbose_name='Domain')
    calling_code = tables.Column(accessor='cc',
                                 verbose_name='Phone Ext.')


MEMORY_DATA = [
    {'name': 'Germany', 'capital': 'Berlin', 'population': 83,
     'currency': 'Euro (€)', 'tld': 'de', 'cc': 49},
    {'name': 'France', 'population': 64, 'currency': 'Euro (€)',
     'tld': 'fr', 'cc': 33},
    {'name': 'Netherlands', 'capital': 'Amsterdam', 'cc': '31'},
    {'name': 'Austria', 'cc': 43, 'currency': 'Euro (€)',
     'population': 8}
]


def test_as_html():
    request = build_request('/')
    table = CountryTable(MEMORY_DATA)
    root = parse(table.as_html(request))
    assert len(root.findall('.//thead/tr')) == 1
    assert len(root.findall('.//thead/tr/th')) == 4
    assert len(root.findall('.//tbody/tr')) == 4
    assert len(root.findall('.//tbody/tr/td')) == 16

    # no data with no empty_text
    table = CountryTable([])
    root = parse(table.as_html(request))
    assert 1 == len(root.findall('.//thead/tr'))
    assert 4 == len(root.findall('.//thead/tr/th'))
    assert 0 == len(root.findall('.//tbody/tr'))

    # no data WITH empty_text
    table = CountryTable([], empty_text='this table is empty')
    root = parse(table.as_html(request))
    assert 1 == len(root.findall('.//thead/tr'))
    assert 4 == len(root.findall('.//thead/tr/th'))
    assert 1 == len(root.findall('.//tbody/tr'))
    assert 1 == len(root.findall('.//tbody/tr/td'))
    assert int(root.find('.//tbody/tr/td').get('colspan')) == len(root.findall('.//thead/tr/th'))
    assert root.find('.//tbody/tr/td').text == 'this table is empty'

    # data without header
    table = CountryTable(MEMORY_DATA, show_header=False)
    root = parse(table.as_html(request))
    assert len(root.findall('.//thead')) == 0
    assert len(root.findall('.//tbody/tr')) == 4
    assert len(root.findall('.//tbody/tr/td')) == 16

    # with custom template
    table = CountryTable([], template='django_tables2/table.html')
    table.as_html(request)


def test_custom_rendering():
    """For good measure, render some actual templates."""
    countries = CountryTable(MEMORY_DATA)
    context = Context({'countries': countries})

    # automatic and manual column verbose names
    template = Template('{% for column in countries.columns %}{{ column }}/'
                        '{{ column.name }} {% endfor %}')
    result = ('Name/name Capital/capital Population Size/population '
              'Phone Ext./calling_code ')
    assert result == template.render(context)

    # row values
    template = Template('{% for row in countries.rows %}{% for value in row %}'
                        '{{ value }} {% endfor %}{% endfor %}')
    result = ('Germany Berlin 83 49 France — 64 33 Netherlands Amsterdam '
              '— 31 Austria — 8 43 ')
    assert result == template.render(context)


@pytest.mark.django_db
class TestQueries(TransactionTestCase):
    def test_as_html_db_queries(self):
        class PersonTable(tables.Table):
            class Meta:
                model = Person

        request = build_request('/')

        with self.assertNumQueries(1):
            PersonTable(Person.objects.all()).as_html(request)

    def test_render_table_db_queries(self):
        Person.objects.create(first_name='brad', last_name='ayers')
        Person.objects.create(first_name='davina', last_name='adisusila')

        class PersonTable(tables.Table):
            class Meta:
                model = Person
                per_page = 1
        request = build_request('/')

        with self.assertNumQueries(2):
            # one query for pagination: .count()
            # one query for page records: .all()[start:end]
            request = build_request('/')
            table = PersonTable(Person.objects.all())
            RequestConfig(request).configure(table)
            # render
            (Template('{% load django_tables2 %}{% render_table table %}')
             .render(Context({'table': table, 'request': request})))


def test_localization_check(settings):
    def get_cond_localized_table(localizeit=None):
        '''
        helper function for defining Table class conditionally
        '''
        class TestTable(tables.Table):
            name = tables.Column(verbose_name="my column", localize=localizeit)
        return TestTable

    simple_test_data = [{'name': 1234.5}]
    expected_results = {
        None: '1234.5',
        False: '1234.5',
        True: '1 234,5'  # non-breaking space
    }
    request = build_request('/')

    # no localization
    html = get_cond_localized_table(None)(simple_test_data).as_html(request)
    assert '<td class="name">{0}</td>'.format(expected_results[None]) in html

    # unlocalize
    html = get_cond_localized_table(False)(simple_test_data).as_html(request)
    assert '<td class="name">{0}</td>'.format(expected_results[False]) in html

    settings.USE_L10N = True
    settings.USE_THOUSAND_SEPARATOR = True

    with translation_override('pl'):
        # with default polish locales and enabled thousand separator
        # 1234.5 is formatted as "1 234,5" with nbsp
        html = get_cond_localized_table(True)(simple_test_data).as_html(request)
        assert '<td class="name">{0}</td>'.format(expected_results[True]) in html

        # with localize = False there should be no formatting
        html = get_cond_localized_table(False)(simple_test_data).as_html(request)
        assert '<td class="name">{0}</td>'.format(expected_results[False]) in html

        # with localize = None and USE_L10N = True
        # there should be the same formatting as with localize = True
        html = get_cond_localized_table(None)(simple_test_data).as_html(request)
        assert '<td class="name">{0}</td>'.format(expected_results[True]) in html


def test_localization_check_in_meta(settings):
    class TableNoLocalize(tables.Table):
        name = tables.Column(verbose_name='my column')

        class Meta:
            default = '---'

    class TableLocalize(tables.Table):
        name = tables.Column(verbose_name='my column')

        class Meta:
            default = '---'
            localize = ('name', )

    class TableUnlocalize(tables.Table):
        name = tables.Column(verbose_name='my column')

        class Meta:
            default = '---'
            unlocalize = ('name', )

    class TableLocalizePrecedence(tables.Table):
        name = tables.Column(verbose_name='my column')

        class Meta:
            default = '---'
            unlocalize = ('name', )
            localize = ('name', )

    simple_test_data = [{'name': 1234.5}]
    expected_results = {
        None: '1234.5',
        False: '1234.5',
        True: '1{0}234,5'.format(' ')  # non-breaking space
    }
    request = build_request('/')
    # No localize
    html = TableNoLocalize(simple_test_data).as_html(request)
    assert '<td class="name">{0}</td>'.format(expected_results[None]) in html

    settings.USE_L10N = True
    settings.USE_THOUSAND_SEPARATOR = True

    with translation_override('pl'):
        # the same as in localization_check.
        # with localization and polish locale we get formatted output
        html = TableNoLocalize(simple_test_data).as_html(request)
        assert '<td class="name">{0}</td>'.format(expected_results[True]) in html

        # localize
        html = TableLocalize(simple_test_data).as_html(request)
        assert '<td class="name">{0}</td>'.format(expected_results[True]) in html

        # unlocalize
        html = TableUnlocalize(simple_test_data).as_html(request)
        assert '<td class="name">{0}</td>'.format(expected_results[False]) in html

        # test unlocalize higher precedence
        html = TableLocalizePrecedence(simple_test_data).as_html(request)
        assert '<td class="name">{0}</td>'.format(expected_results[False]) in html


def test_localization_of_pagination_string():
    class Table(tables.Table):
        foo = tables.Column(verbose_name='my column')
        bar = tables.Column()

        class Meta:
            default = '---'

    table = Table(map(lambda x: [x, x + 100], range(40)))
    request = build_request('/')
    RequestConfig(request, paginate={'per_page': 10}).configure(table)

    with translation_override('en'):
        assert 'Page 1 of 4' in table.as_html(request)

    with translation_override('nl'):
        assert 'Pagina 1 van 4' in table.as_html(request)

    with translation_override('it'):
        assert 'Pagina 1 di 4' in table.as_html(request)

    with translation_override('nb'):
        assert 'Side 1 av 4' in table.as_html(request)


class BootstrapTable(CountryTable):
    class Meta:
        template = 'django_tables2/bootstrap.html'
        prefix = 'bootstrap-'
        per_page = 2


def test_boostrap_template():
    table = BootstrapTable(MEMORY_DATA)
    request = build_request('/')
    RequestConfig(request).configure(table)

    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': request, 'table': table}))
    root = parse(html)
    assert len(root.findall('.//thead/tr')) == 1
    assert len(root.findall('.//thead/tr/th')) == 4
    assert len(root.findall('.//tbody/tr')) == 2
    assert len(root.findall('.//tbody/tr/td')) == 8

    assert root.find('./ul[@class="pager list-inline"]/li[@class="cardinality"]/small').text.strip() == 'Page 1 of 2'
    # make sure the link is prefixed
    assert root.find('./ul[@class="pager list-inline"]/li[@class="next"]/a').get('href') == '?bootstrap-page=2'


class SemanticTable(CountryTable):
    class Meta:
        template = 'django_tables2/semantic.html'
        prefix = 'semantic-'
        per_page = 2


def test_semantic_template():
    table = SemanticTable(MEMORY_DATA)
    request = build_request('/')
    RequestConfig(request).configure(table)

    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': request, 'table': table}))
    root = parse(html)
    assert len(root.findall('.//thead/tr')) == 1
    assert len(root.findall('.//thead/tr/th')) == 4
    assert len(root.findall('.//tbody/tr')) == 2
    assert len(root.findall('.//tbody/tr/td')) == 8

    pager = './/tfoot/tr/th/div[@class="ui right floated pagination menu"]/div[@class="item"]'
    assert root.find(pager).text.strip() == 'Page 1 of 2'
    # make sure the link is prefixed
    next_page = './/tfoot/tr/th/div[@class="ui right floated pagination menu"]/a[@class="icon item"]'
    assert root.find(next_page).get('href') == '?semantic-page=2'
