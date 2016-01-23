# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.template import Context

import django_tables2 as tables


def test_should_handle_context_on_table():
    class TestTable(tables.Table):
        col_code = tables.TemplateColumn(template_code="code:{{ record.col }}{{ STATIC_URL }}")
        col_name = tables.TemplateColumn(template_name="test_template_column.html")

    table = TestTable([{"col": "brad"}])
    assert table.rows[0]["col_code"] == "code:brad"
    assert table.rows[0]["col_name"] == "name:brad"
    table.context = Context({"STATIC_URL": "/static/"})
    assert table.rows[0]["col_code"] == "code:brad/static/"
    assert table.rows[0]["col_name"] == "name:brad/static/"


def test_should_support_default():
    class Table(tables.Table):
        foo = tables.TemplateColumn("default={{ default }}", default="bar")

    table = Table([{}])
    assert table.rows[0]["foo"] == "default=bar"


def test_should_support_value():
    class Table(tables.Table):
        foo = tables.TemplateColumn("value={{ value }}")

    table = Table([{"foo": "bar"}])
    assert table.rows[0]["foo"] == "value=bar"


def test_should_support_column():
    class Table(tables.Table):
        tcol = tables.TemplateColumn("column={{ column.name }}")

    table = Table([{'foo': 'bar'}])
    assert table.rows[0]['tcol'] == 'column=tcol'


def test_should_raise_when_called_without_template():
    with pytest.raises(ValueError):
        class Table(tables.Table):
            col = tables.TemplateColumn()
