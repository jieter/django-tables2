# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.template import Context

import django_tables2 as tables


def test_should_handle_context_on_table():
    class TestTable(tables.Table):
        col_code = tables.TemplateColumn(template_code='code:{{ record.col }}-{{ foo }}')
        col_name = tables.TemplateColumn(template_name='test_template_column.html')

    table = TestTable([{'col': 'brad'}])
    assert table.rows[0].get_cell('col_code') == 'code:brad-'
    assert table.rows[0].get_cell('col_name') == 'name:brad-empty\n'

    table.context = Context({'foo': 'author'})
    assert table.rows[0].get_cell('col_code') == 'code:brad-author'
    assert table.rows[0].get_cell('col_name') == 'name:brad-author\n'


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


def test_should_support_column():
    class Table(tables.Table):
        tcol = tables.TemplateColumn("column={{ column.name }}")

    table = Table([{'foo': 'bar'}])
    assert table.rows[0].get_cell('tcol') == 'column=tcol'


def test_should_raise_when_called_without_template():
    with pytest.raises(ValueError):
        class Table(tables.Table):
            col = tables.TemplateColumn()
