# -*- coding: utf8 -*-
"""Test template specific functionality.

Make sure tables expose their functionality to templates right. This
generally about testing "out"-functionality of the tables, whether
via templates or otherwise. Whether a test belongs here or, say, in
``test_basic``, is not always a clear-cut decision.
"""

from django.template import Template, Context
from django.http import HttpRequest
import django_tables as tables
from attest import Tests, Assert
from xml.etree import ElementTree as ET

templates = Tests()


@templates.context
def context():
    class Context(object):
        class CountryTable(tables.Table):
            name = tables.Column()
            capital = tables.Column(sortable=False)
            population = tables.Column(verbose_name='Population Size')
            currency = tables.Column(visible=False)
            tld = tables.Column(visible=False, verbose_name='Domain')
            calling_code = tables.Column(accessor='cc',
                                         verbose_name='Phone Ext.')

        data = [
            {'name': 'Germany', 'capital': 'Berlin', 'population': 83,
             'currency': 'Euro (€)', 'tld': 'de', 'cc': 49},
            {'name': 'France', 'population': 64, 'currency': 'Euro (€)',
             'tld': 'fr', 'cc': 33},
            {'name': 'Netherlands', 'capital': 'Amsterdam', 'cc': '31'},
            {'name': 'Austria', 'cc': 43, 'currency': 'Euro (€)',
             'population': 8}
        ]
    yield Context


@templates.test
def as_html(context):
    table = context.CountryTable(context.data)
    root = ET.fromstring(table.as_html())    
    Assert(len(root.findall('.//thead/tr'))) == 1
    Assert(len(root.findall('.//thead/tr/th'))) == 4
    Assert(len(root.findall('.//tbody/tr'))) == 4
    Assert(len(root.findall('.//tbody/tr/td'))) == 16
    
    # no data with no empty_text
    table = context.CountryTable([])
    root = ET.fromstring(table.as_html())
    Assert(1) == len(root.findall('.//thead/tr'))
    Assert(4) == len(root.findall('.//thead/tr/th'))
    Assert(0) == len(root.findall('.//tbody/tr'))
    
    # no data WITH empty_text
    table = context.CountryTable([], empty_text='this table is empty')
    root = ET.fromstring(table.as_html())
    Assert(1) == len(root.findall('.//thead/tr'))
    Assert(4) == len(root.findall('.//thead/tr/th'))
    Assert(1) == len(root.findall('.//tbody/tr'))
    Assert(1) == len(root.findall('.//tbody/tr/td'))
    Assert(int(root.find('.//tbody/tr/td').attrib['colspan'])) == len(root.findall('.//thead/tr/th'))
    Assert(root.find('.//tbody/tr/td').text) == 'this table is empty'


@templates.test
def custom_rendering(context):
    """For good measure, render some actual templates."""
    countries = context.CountryTable(context.data)
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
def templatetag(context):
    # ensure it works with a multi-order-by
    table = context.CountryTable(context.data, order_by=('name', 'population'))
    t = Template('{% load django_tables %}{% render_table table %}')
    html = t.render(Context({'request': HttpRequest(), 'table': table}))
    
    root = ET.fromstring(html)    
    Assert(len(root.findall('.//thead/tr'))) == 1
    Assert(len(root.findall('.//thead/tr/th'))) == 4
    Assert(len(root.findall('.//tbody/tr'))) == 4
    Assert(len(root.findall('.//tbody/tr/td'))) == 16
    
    # no data with no empty_text
    table = context.CountryTable([])
    t = Template('{% load django_tables %}{% render_table table %}')
    html = t.render(Context({'request': HttpRequest(), 'table': table}))
    root = ET.fromstring(html)    
    Assert(len(root.findall('.//thead/tr'))) == 1
    Assert(len(root.findall('.//thead/tr/th'))) == 4
    Assert(len(root.findall('.//tbody/tr'))) == 0
    
    # no data WITH empty_text
    table = context.CountryTable([], empty_text='this table is empty')
    t = Template('{% load django_tables %}{% render_table table %}')
    html = t.render(Context({'request': HttpRequest(), 'table': table}))
    root = ET.fromstring(html)    
    Assert(len(root.findall('.//thead/tr'))) == 1
    Assert(len(root.findall('.//thead/tr/th'))) == 4
    Assert(len(root.findall('.//tbody/tr'))) == 1
    Assert(len(root.findall('.//tbody/tr/td'))) == 1
    Assert(int(root.find('.//tbody/tr/td').attrib['colspan'])) == len(root.findall('.//thead/tr/th'))
    Assert(root.find('.//tbody/tr/td').text) == 'this table is empty'
    
    
    
