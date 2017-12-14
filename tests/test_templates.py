# coding: utf-8
from __future__ import unicode_literals

from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings
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


class TemplateTest(TestCase):
    @override_settings(DJANGO_TABLES2_TEMPLATE='foo/bar.html')
    def test_template_override_in_settings(self):
        class Table(tables.Table):
            column = tables.Column()

        table = Table({})
        assert table.template == 'foo/bar.html'

    def test_as_html(self):
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

    def test_custom_rendering(self):
        '''For good measure, render some actual templates.'''
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


class TestQueries(TestCase):
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


class TemplateLocalizeTest(TestCase):
    simple_test_data = [{'name': 1234.5}]
    expected_results = {
        None: '1234.5',
        False: '1234.5',
        True: '1 234,5'  # non-breaking space
    }

    def assert_cond_localized_table(self, localizeit=None, expected=None):
        '''
        helper function for defining Table class conditionally
        '''
        class TestTable(tables.Table):
            name = tables.Column(verbose_name="my column", localize=localizeit)

        self.assert_table_localization(TestTable, expected)

    def assert_table_localization(self, TestTable, expected):
        html = TestTable(self.simple_test_data).as_html(build_request())
        self.assertIn(
            '<td class="name">{0}</td>'.format(self.expected_results[expected]),
            html
        )

    def test_localization_check(self):
        self.assert_cond_localized_table(None, None)
        # unlocalize
        self.assert_cond_localized_table(False, False)

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_localization_different_locale(self):
        with translation_override('pl'):
            # with default polish locales and enabled thousand separator
            # 1234.5 is formatted as "1 234,5" with nbsp
            self.assert_cond_localized_table(True, True)

            # with localize = False there should be no formatting
            self.assert_cond_localized_table(False, False)

            # with localize = None and USE_L10N = True
            # there should be the same formatting as with localize = True
            self.assert_cond_localized_table(None, True)

    def test_localization_check_in_meta(self):
        class TableNoLocalize(tables.Table):
            name = tables.Column(verbose_name='my column')

            class Meta:
                default = '---'

        self.assert_table_localization(TableNoLocalize, None)

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_localization_check_in_meta_different_locale(self):
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

        with translation_override('pl'):
            # the same as in localization_check.
            # with localization and polish locale we get formatted output
            self.assert_table_localization(TableNoLocalize, True)

            # localize
            self.assert_table_localization(TableLocalize, True)

            # unlocalize
            self.assert_table_localization(TableUnlocalize, False)

            # test unlocalize has higher precedence
            self.assert_table_localization(TableLocalizePrecedence, False)

    def test_localization_of_pagination_string(self):
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


class BootstrapTemplateTest(SimpleTestCase):
    def test_boostrap_template(self):
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

        self.assertEquals(
            root.find('./ul[@class="pager list-inline"]/li[@class="cardinality"]/small').text.strip(),
            'Page 1 of 2'
        )
        # make sure the link is prefixed
        self.assertEquals(
            root.find('./ul[@class="pager list-inline"]/li[@class="next"]/a').get('href'),
            '?bootstrap-page=2'
        )

    def test_bootstrap_responsive_template(self):
        class BootstrapResponsiveTable(BootstrapTable):
            class Meta(BootstrapTable.Meta):
                template = 'django_tables2/bootstrap-responsive.html'

        table = BootstrapResponsiveTable(MEMORY_DATA)
        request = build_request('/')
        RequestConfig(request).configure(table)

        template = Template('{% load django_tables2 %}{% render_table table %}')
        html = template.render(Context({'request': request, 'table': table}))
        root = parse(html)
        assert len(root.findall('.//thead/tr')) == 1
        assert len(root.findall('.//thead/tr/th')) == 4
        assert len(root.findall('.//tbody/tr')) == 2
        assert len(root.findall('.//tbody/tr/td')) == 8

        pager = './/ul/li[@class="cardinality"]/small'
        assert root.find(pager).text.strip() == 'Page 1 of 2'


class SemanticTemplateTest(SimpleTestCase):
    def test_semantic_template(self):
        class SemanticTable(CountryTable):
            class Meta:
                template = 'django_tables2/semantic.html'
                prefix = 'semantic-'
                per_page = 2

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
