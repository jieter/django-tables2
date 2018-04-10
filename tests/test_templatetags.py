# coding: utf-8
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.template import Context, RequestContext, Template, TemplateSyntaxError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import six
from django.utils.six.moves.urllib.parse import parse_qs

from django_tables2 import RequestConfig, Table, TemplateColumn
from django_tables2.utils import AttributeDict

from .app.models import Region
from .test_templates import MEMORY_DATA, CountryTable
from .utils import build_request, parse


class RenderTableTagTest(TestCase):

    def test_invalid_type(self):
        template = Template('{% load django_tables2 %}{% render_table table %}')

        with self.assertRaises(ValueError):
            template.render(Context({
                'request': build_request(),
                'table': dict()
            }))

    def test_basic(self):
        request = build_request('/')
        # ensure it works with a multi-order-by
        table = CountryTable(MEMORY_DATA, order_by=('name', 'population'))
        RequestConfig(request).configure(table)
        template = Template('{% load django_tables2 %}{% render_table table %}')
        html = template.render(Context({'request': request, 'table': table}))

        root = parse(html)
        self.assertEqual(len(root.findall('.//thead/tr')), 1)
        self.assertEqual(len(root.findall('.//thead/tr/th')), 4)
        self.assertEqual(len(root.findall('.//tbody/tr')), 4)
        self.assertEqual(len(root.findall('.//tbody/tr/td')), 16)

    def test_does_not_mutate_context(self):
        '''
        Make sure the tag does not change the context of the template the tag is called from
        https://github.com/jieter/django-tables2/issues/547
        '''
        class MyTable(Table):
            col = TemplateColumn(template_code='{{ value }}')

        table = MyTable([{'col': 'foo'}, {'col': 'bar'}], template_name='minimal.html')
        template = Template(
            '{% load django_tables2 %}'
            '{% with "foo" as table %}{{ table }}{% render_table mytable %}\n{{ table }}{% endwith %}'
        )

        html = template.render(Context({
            'request': build_request(),
            'mytable': table,
        }))
        lines = html.splitlines()
        self.assertEqual(lines[0], 'foo')
        self.assertEqual(lines[-1], 'foo')

    def test_table_context_is_RequestContext(self):
        class MyTable(Table):
            col = TemplateColumn(template_code='{{ value }}')

        template = Template('{% load django_tables2 %}{% render_table table %}')
        html = template.render(Context({
            'request': build_request(),
            'table': MyTable([], template_name='csrf.html')
        }))
        input_tag = parse(html)
        self.assertEqual(input_tag.get('type'), 'hidden')
        self.assertEqual(input_tag.get('name'), 'csrfmiddlewaretoken')
        self.assertEqual(len(input_tag.get('value')), 64)

    def test_no_data_without_empty_text(self):
        table = CountryTable([])
        template = Template('{% load django_tables2 %}{% render_table table %}')
        html = template.render(Context({'request': build_request('/'), 'table': table}))
        root = parse(html)
        self.assertEqual(len(root.findall('.//thead/tr')), 1)
        self.assertEqual(len(root.findall('.//thead/tr/th')), 4)
        self.assertEqual(len(root.findall('.//tbody/tr')), 0)

    def test_no_data_with_empty_text(self):
        # no data WITH empty_text
        request = build_request('/')
        table = CountryTable([], empty_text='this table is empty')
        RequestConfig(request).configure(table)
        template = Template('{% load django_tables2 %}{% render_table table %}')
        html = template.render(Context({'request': request, 'table': table}))

        root = parse(html)
        self.assertEqual(len(root.findall('.//thead/tr')), 1)
        self.assertEqual(len(root.findall('.//thead/tr/th')), 4)
        self.assertEqual(len(root.findall('.//tbody/tr')), 1)
        self.assertEqual(len(root.findall('.//tbody/tr/td')), 1)
        self.assertEqual(int(root.find('.//tbody/tr/td').get('colspan')), len(root.findall('.//thead/tr/th')))
        self.assertEqual(root.find('.//tbody/tr/td').text, 'this table is empty')

    @override_settings(DEBUG=True)
    def test_missing_variable(self):
        # variable that doesn't exist (issue #8)
        template = Template('{% load django_tables2 %}{% render_table this_doesnt_exist %}')
        with self.assertRaises(ValueError):
            template.render(Context())

    @override_settings(DEBUG=False)
    def test_missing_variable_debug_False(self):
        template = Template('{% load django_tables2 %}{% render_table this_doesnt_exist %}')
        # Should still be noisy with debug off
        with self.assertRaises(ValueError):
            template.render(Context())

    def test_should_support_template_argument(self):
        table = CountryTable(MEMORY_DATA, order_by=('name', 'population'))
        template = Template('{% load django_tables2 %}'
                            '{% render_table table "dummy.html" %}')

        context = RequestContext(build_request(), {'table': table})
        self.assertEqual(template.render(context), 'dummy template contents\n')

    def test_template_argument_list(self):
        template = Template('{% load django_tables2 %}'
                            '{% render_table table template_list %}')

        context = RequestContext(build_request(), {
            'table': CountryTable(MEMORY_DATA, order_by=('name', 'population')),
            'template_list': ('dummy.html', 'child/foo.html')
        })
        self.assertEqual(template.render(context), 'dummy template contents\n')

    def test_render_table_supports_queryset(self):
        for name in ('Mackay', 'Brisbane', 'Maryborough'):
            Region.objects.create(name=name)
        template = Template('{% load django_tables2 %}{% render_table qs %}')
        html = template.render(Context({
            'qs': Region.objects.all(),
            'request': build_request('/')
        }))

        root = parse(html)
        self.assertEqual([e.text for e in root.findall('.//thead/tr/th/a')], ['ID', 'Name', 'Mayor'])
        td = [[td.text for td in tr.findall('td')] for tr in root.findall('.//tbody/tr')]
        db = []
        for region in Region.objects.all():
            db.append([six.text_type(region.id), region.name, "—"])
        self.assertEqual(td, db)


class QuerystringTagTest(SimpleTestCase):
    def test_basic(self):
        template = Template('{% load django_tables2 %}'
                            '<b>{% querystring "name"="Brad" foo.bar=value %}</b>')

        # Should be something like: <root>?name=Brad&amp;a=b&amp;c=5&amp;age=21</root>
        xml = template.render(Context({
            'request': build_request('/?a=b&name=dog&c=5'),
            'foo': {'bar': 'age'},
            'value': 21,
        }))

        # Ensure it's valid XML, retrieve the URL
        url = parse(xml).text

        qs = parse_qs(url[1:])  # everything after the ?
        self.assertEqual(qs['name'], ['Brad'])
        self.assertEqual(qs['age'], ['21'])
        self.assertEqual(qs['a'], ['b'])
        self.assertEqual(qs['c'], ['5'])

    def test_requires_request(self):
        template = Template('{% load django_tables2 %}{% querystring "name"="Brad" %}')
        with self.assertRaises(ImproperlyConfigured):
            template.render(Context())

    def test_supports_without(self):
        context = Context({
            'request': build_request('/?a=b&name=dog&c=5'),
            'a_var': 'a',
        })

        template = Template('{% load django_tables2 %}'
                            '<b>{% querystring "name"="Brad" without a_var %}</b>')
        url = parse(template.render(context)).text
        qs = parse_qs(url[1:])  # trim the ?
        self.assertEqual(set(qs.keys()), set(['name', 'c']))

    def test_only_without(self):
        context = Context({
            'request': build_request('/?a=b&name=dog&c=5'),
            'a_var': 'a',
        })
        template = Template('{% load django_tables2 %}'
                            '<b>{% querystring without "a" "name" %}</b>')
        url = parse(template.render(context)).text
        qs = parse_qs(url[1:])  # trim the ?
        self.assertEqual(set(qs.keys()), set(["c"]))

    def test_querystring_syntax_error(self):
        with self.assertRaises(TemplateSyntaxError):
            Template('{% load django_tables2 %}{% querystring foo= %}')

    def test_querystring_as_var(self):
        def assert_querystring_asvar(template_code, expected):
            template = Template(
                '{% load django_tables2 %}' +
                '<b>{% querystring ' + template_code + ' %}</b>' +
                '<strong>{{ varname }}</strong>'
            )

            # Should be something like: <root>?name=Brad&amp;a=b&amp;c=5&amp;age=21</root>
            xml = template.render(Context({
                'request': build_request('/?a=b'),
                'foo': {'bar': 'age'},
                'value': 21,
            }))
            self.assertIn('<b></b>', xml)
            qs = parse(xml).xpath('.//strong')[0].text[1:]
            self.assertEqual(parse_qs(qs), expected)

        tests = (
            ('"name"="Brad" as=varname', dict(name=['Brad'], a=['b'])),
            ('as=varname "name"="Brad"', dict(name=['Brad'], a=['b'])),
            ('"name"="Brad" as=varname without "a" ', dict(name=['Brad']))
        )

        for argstr, expected in tests:
            assert_querystring_asvar(argstr, expected)

    def test_export_url_tag(self):
        template = Template('{% load django_tables2 %}{% export_url "csv" %}')
        html = template.render(Context({'request': build_request('?q=foo')}))
        self.assertEqual(dict(parse_qs(html[1:])), dict(parse_qs('q=foo&amp;_export=csv')))

        # using a template context variable
        template = Template('{% load django_tables2 %}{% export_url format %}')
        html = template.render(Context({'request': build_request('?q=foo'), 'format': 'xls'}))
        self.assertEqual(dict(parse_qs(html[1:])), dict(parse_qs('q=foo&amp;_export=xls')))


    def test_render_attributes_test(self):
        template = Template('{% load django_tables2 %}{% render_attrs attrs class="table" %}')
        html = template.render(Context({}))
        self.assertEqual(html, 'class="table"')

        html = template.render(Context({
            'attrs': AttributesDict({'class': 'table table-striped'})
        }))
        self.assertEqual(html, 'class="table table-striped"')


class TitleTagTest(SimpleTestCase):
    def test_should_only_apply_to_words_without_uppercase_letters(self):
        expectations = {
            'a brown fox': 'A Brown Fox',
            'a brown foX': 'A Brown foX',
            'black FBI': 'Black FBI',
            'f.b.i': 'F.B.I',
            'start 6pm': 'Start 6pm',

            # Some cyrillic samples
            'руда лисиця': 'Руда Лисиця',
            'руда лисицЯ': 'Руда лисицЯ',
            'діяльність СБУ': 'Діяльність СБУ',
            'а.б.в': 'А.Б.В',
            'вага 6кг': 'Вага 6кг',
            'у 80-их роках': 'У 80-их Роках',
        }

        for raw, expected in expectations.items():
            template = Template('{% load django_tables2 %}{{ x|title }}')
            assert template.render(Context({'x': raw})), expected
