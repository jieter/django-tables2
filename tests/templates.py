# -*- coding: utf8 -*-
from django.template import Template, Context, VariableDoesNotExist
from django.test.client import RequestFactory
from django.http import HttpRequest
from django.conf import settings
from urlparse import parse_qs
import django_tables2 as tables
from attest import Tests, Assert
from xml.etree import ElementTree as ET
from django.utils.translation import ugettext_lazy as _


templates = Tests()


class CountryTable(tables.Table):
    name = tables.Column()
    capital = tables.Column(sortable=False, verbose_name=_("Capital"))
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
    Assert(len(root.findall('.//thead/tr'))) == 1
    Assert(len(root.findall('.//thead/tr/th'))) == 4
    Assert(len(root.findall('.//tbody/tr'))) == 4
    Assert(len(root.findall('.//tbody/tr/td'))) == 16

    # no data with no empty_text
    table = CountryTable([])
    root = ET.fromstring(table.as_html())
    Assert(1) == len(root.findall('.//thead/tr'))
    Assert(4) == len(root.findall('.//thead/tr/th'))
    Assert(0) == len(root.findall('.//tbody/tr'))

    # no data WITH empty_text
    table = CountryTable([], empty_text='this table is empty')
    root = ET.fromstring(table.as_html())
    Assert(1) == len(root.findall('.//thead/tr'))
    Assert(4) == len(root.findall('.//thead/tr/th'))
    Assert(1) == len(root.findall('.//tbody/tr'))
    Assert(1) == len(root.findall('.//tbody/tr/td'))
    Assert(int(root.find('.//tbody/tr/td').attrib['colspan'])) == len(root.findall('.//thead/tr/th'))
    Assert(root.find('.//tbody/tr/td').text) == 'this table is empty'


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
    Assert(result) == template.render(context)

    # row values
    template = Template('{% for row in countries.rows %}{% for value in row %}'
                        '{{ value }} {% endfor %}{% endfor %}')
    result = ('Germany Berlin 83 49 France None 64 33 Netherlands Amsterdam '
              'None 31 Austria None 8 43 ')
    Assert(result) == template.render(context)


@templates.test
def render_table_templatetag():
    # ensure it works with a multi-order-by
    table = CountryTable(MEMORY_DATA, order_by=('name', 'population'))
    t = Template('{% load django_tables2 %}{% render_table table %}')
    html = t.render(Context({'request': HttpRequest(), 'table': table}))

    root = ET.fromstring(html)
    Assert(len(root.findall('.//thead/tr'))) == 1
    Assert(len(root.findall('.//thead/tr/th'))) == 4
    Assert(len(root.findall('.//tbody/tr'))) == 4
    Assert(len(root.findall('.//tbody/tr/td'))) == 16

    # no data with no empty_text
    table = CountryTable([])
    t = Template('{% load django_tables2 %}{% render_table table %}')
    html = t.render(Context({'request': HttpRequest(), 'table': table}))
    root = ET.fromstring(html)
    Assert(len(root.findall('.//thead/tr'))) == 1
    Assert(len(root.findall('.//thead/tr/th'))) == 4
    Assert(len(root.findall('.//tbody/tr'))) == 0

    # no data WITH empty_text
    table = CountryTable([], empty_text='this table is empty')
    t = Template('{% load django_tables2 %}{% render_table table %}')
    html = t.render(Context({'request': HttpRequest(), 'table': table}))
    root = ET.fromstring(html)
    Assert(len(root.findall('.//thead/tr'))) == 1
    Assert(len(root.findall('.//thead/tr/th'))) == 4
    Assert(len(root.findall('.//tbody/tr'))) == 1
    Assert(len(root.findall('.//tbody/tr/td'))) == 1
    Assert(int(root.find('.//tbody/tr/td').attrib['colspan'])) == len(root.findall('.//thead/tr/th'))
    Assert(root.find('.//tbody/tr/td').text) == 'this table is empty'

    # variable that doesn't exist (issue #8)
    t = Template('{% load django_tables2 %}{% render_table this_doesnt_exist %}')
    with Assert.raises(ValueError):
        settings.DEBUG = True
        t.render(Context())

    # Should be silent with debug off
    settings.DEBUG = False
    t.render(Context())


@templates.test
def querystring_templatetag():
    factory = RequestFactory()
    t = Template('{% load django_tables2 %}{% querystring "name"="Brad" foo.bar=value %}')
    # Should be something like: ?name=Brad&a=b&c=5&age=21
    url = t.render(Context({
        "request": factory.get('/?a=b&name=dog&c=5'),
        "foo": {"bar": "age"},
        "value": 21,
    }))
    qs = parse_qs(url[1:])  # everything after the ?
    Assert(qs["name"]) == ["Brad"]
    Assert(qs["age"]) == ["21"]
    Assert(qs["a"]) == ["b"]
    Assert(qs["c"]) == ["5"]
