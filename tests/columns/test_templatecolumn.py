# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.template import Context, Template

import django_tables2 as tables

from ..utils import build_request


def test_should_render_in_pinned_row():
    class TestOnlyPinnedTable(tables.Table):
        foo = tables.TemplateColumn('value={{ value }}')

        def __init__(self, data):
            self.pinned = data
            revised_data = []

            super(TestOnlyPinnedTable, self).__init__(revised_data)

        def get_top_pinned_data(self):
            return self.pinned

    table = TestOnlyPinnedTable([{'foo': 'bar'}])
    for row in table.rows:
        assert row.get_cell('foo') == 'value=bar'

    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': build_request(), 'table': table}))

    assert '<td class="foo">value=bar</td>' in html


def test_should_handle_context_on_table():
    class TestTable(tables.Table):
        col_code = tables.TemplateColumn(template_code='code:{{ record.col }}-{{ foo }}')
        col_name = tables.TemplateColumn(template_name='test_template_column.html')
        col_context = tables.TemplateColumn(template_code="{{ label }}:{{ record.col }}-{{ foo }}",
                                            extra_context={'label': 'label'})

    table = TestTable([{'col': 'brad'}])
    assert table.rows[0].get_cell('col_code') == 'code:brad-'
    assert table.rows[0].get_cell('col_name') == 'name:brad-empty\n'
    assert table.rows[0].get_cell("col_context") == "label:brad-"

    table.context = Context({'foo': 'author'})
    assert table.rows[0].get_cell('col_code') == 'code:brad-author'
    assert table.rows[0].get_cell('col_name') == 'name:brad-author\n'
    assert table.rows[0].get_cell("col_context") == "label:brad-author"

    # new table and render using the 'render_table' template tag.
    table = TestTable([{'col': 'brad'}])
    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': build_request(), 'table': table, 'foo': 'author'}))

    assert '<td class="col_name">name:brad-author\n</td>' in html


def test_should_support_default():
    class Table(tables.Table):
        foo = tables.TemplateColumn('default={{ default }}', default='bar')

    table = Table([{}])
    assert table.rows[0].get_cell('foo') == 'default=bar'


def test_should_support_value():
    class Table(tables.Table):
        foo = tables.TemplateColumn('value={{ value }}')

    table = Table([{'foo': 'bar'}])
    assert table.rows[0].get_cell('foo') == 'value=bar'

    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': build_request(), 'table': table}))

    assert '<td class="foo">value=bar</td>' in html


def test_should_support_column():
    class Table(tables.Table):
        tcol = tables.TemplateColumn('column={{ column.name }}')

    table = Table([{'foo': 'bar'}])
    assert table.rows[0].get_cell('tcol') == 'column=tcol'


def test_should_raise_when_called_without_template():
    with pytest.raises(ValueError):
        class Table(tables.Table):
            col = tables.TemplateColumn()


def test_should_support_value_with_curly_braces():
    '''
    https://github.com/bradleyayers/django-tables2/issues/441
    '''
    class Table(tables.Table):
        track = tables.TemplateColumn('track: {{ value }}')

    table = Table([{'track': 'Beat it {Freestyle}'}])
    assert table.rows[0].get_cell('track') == 'track: Beat it {Freestyle}'


def test_should_strip_tags_for_value():
    class Table(tables.Table):
        track = tables.TemplateColumn('<span>{{ value }}</span>')

    table = Table([{'track': 'Space Oddity'}])

    assert list(table.as_values()) == [['Track'], ['Space Oddity']]
