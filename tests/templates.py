# -*- coding: utf-8 -*-
from django.template import Template, RequestContext, Context, VariableDoesNotExist
from django.test.client import RequestFactory
from django.http import HttpRequest
from django.conf import settings
from urlparse import parse_qs
import django_tables2 as tables
from attest import Tests, Assert
from xml.etree import ElementTree as ET
from django.utils.translation import ugettext_lazy


templates = Tests()


class CountryTable(tables.Table):
    name = tables.Column()
    capital = tables.Column(sortable=False,
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


@templates.test
def as_html():
    table = CountryTable(MEMORY_DATA)
    root = ET.fromstring(table.as_html())
    assert len(root.findall('.//thead/tr'))== 1
    assert len(root.findall('.//thead/tr/th')) == 4
    assert len(root.findall('.//tbody/tr')) == 4
    assert len(root.findall('.//tbody/tr/td')) == 16

    # no data with no empty_text
    table = CountryTable([])
    root = ET.fromstring(table.as_html())
    assert 1 == len(root.findall('.//thead/tr'))
    assert 4 == len(root.findall('.//thead/tr/th'))
    assert 0 == len(root.findall('.//tbody/tr'))

    # no data WITH empty_text
    table = CountryTable([], empty_text='this table is empty')
    root = ET.fromstring(table.as_html())
    assert 1 == len(root.findall('.//thead/tr'))
    assert 4 == len(root.findall('.//thead/tr/th'))
    assert 1 == len(root.findall('.//tbody/tr'))
    assert 1 == len(root.findall('.//tbody/tr/td'))
    assert int(root.find('.//tbody/tr/td').attrib['colspan']) == len(root.findall('.//thead/tr/th'))
    assert root.find('.//tbody/tr/td').text == 'this table is empty'

    # with custom template
    table = CountryTable([], template="django_tables2/table.html")
    table.as_html()


@templates.test
def custom_rendering():
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
    result = ('Germany Berlin 83 49 France None 64 33 Netherlands Amsterdam '
              'None 31 Austria None 8 43 ')
    assert result == template.render(context)


@templates.test
def render_table_templatetag():
    # ensure it works with a multi-order-by
    table = CountryTable(MEMORY_DATA, order_by=('name', 'population'))
    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': HttpRequest(), 'table': table}))

    root = ET.fromstring(html)
    assert len(root.findall('.//thead/tr')) == 1
    assert len(root.findall('.//thead/tr/th')) == 4
    assert len(root.findall('.//tbody/tr')) == 4
    assert len(root.findall('.//tbody/tr/td')) == 16

    # no data with no empty_text
    table = CountryTable([])
    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': HttpRequest(), 'table': table}))
    root = ET.fromstring(html)
    assert len(root.findall('.//thead/tr')) == 1
    assert len(root.findall('.//thead/tr/th')) == 4
    assert len(root.findall('.//tbody/tr')) == 0

    # no data WITH empty_text
    table = CountryTable([], empty_text='this table is empty')
    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': HttpRequest(), 'table': table}))
    root = ET.fromstring(html)
    assert len(root.findall('.//thead/tr')) == 1
    assert len(root.findall('.//thead/tr/th')) == 4
    assert len(root.findall('.//tbody/tr')) == 1
    assert len(root.findall('.//tbody/tr/td')) == 1
    assert int(root.find('.//tbody/tr/td').attrib['colspan']) == len(root.findall('.//thead/tr/th'))
    assert root.find('.//tbody/tr/td').text == 'this table is empty'

    # variable that doesn't exist (issue #8)
    template = Template('{% load django_tables2 %}'
                        '{% render_table this_doesnt_exist %}')
    with Assert.raises(ValueError):
        settings.DEBUG = True
        template.render(Context())

    # Should still be noisy with debug off
    with Assert.raises(ValueError):
        settings.DEBUG = False
        template.render(Context())


@templates.test
def render_table_should_support_template_argument():
    table = CountryTable(MEMORY_DATA, order_by=('name', 'population'))
    template = Template('{% load django_tables2 %}'
                        '{% render_table table "dummy.html" %}')
    request = RequestFactory().get('/')
    context = RequestContext(request, {'table': table})
    settings.DEBUG = True
    assert template.render(context) == 'dummy template contents\n'


@templates.test
def querystring_templatetag():
    factory = RequestFactory()
    template = Template('{% load django_tables2 %}'
                        '{% querystring "name"="Brad" foo.bar=value %}')
    # Should be something like: ?name=Brad&a=b&c=5&age=21
    url = template.render(Context({
        "request": factory.get('/?a=b&name=dog&c=5'),
        "foo": {"bar": "age"},
        "value": 21,
    }))
    qs = parse_qs(url[1:])  # everything after the ?
    assert qs["name"] == ["Brad"]
    assert qs["age"] == ["21"]
    assert qs["a"] == ["b"]
    assert qs["c"] == ["5"]
