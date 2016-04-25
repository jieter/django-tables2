# coding: utf-8
# pylint: disable=R0912,E0102
from __future__ import unicode_literals

import django_tables2 as tables

from ..utils import attrs


def test_new_attrs_should_be_supported():
    class TestTable(tables.Table):
        col1 = tables.CheckBoxColumn(attrs=dict(th__input={'th_key': 'th_value'},
                                                td__input={'td_key': 'td_value'}))
        col2 = tables.CheckBoxColumn(attrs=dict(input={'key': 'value'}))

    table = TestTable([{'col1': 'data', 'col2': 'data'}])
    assert attrs(table.columns['col1'].header) == {'type': 'checkbox', 'th_key': 'th_value'}
    assert attrs(table.rows[0].get_cell('col1')) == {
        'type': 'checkbox',
        'td_key': 'td_value',
        'value': 'data',
        'name': 'col1'
    }
    assert attrs(table.columns['col2'].header) == {'type': 'checkbox', 'key': 'value'}
    assert attrs(table.rows[0].get_cell('col2')) == {
        'type': 'checkbox',
        'key': 'value',
        'value': 'data',
        'name': 'col2'
    }


def test_column_is_checked():
    class TestTable(tables.Table):
        col = tables.CheckBoxColumn(attrs={'name': 'col'}, checked='is_selected')

    table = TestTable([
        {'col': '1', 'is_selected': True},
        {'col': '2', 'is_selected': False}
    ])
    assert attrs(table.rows[0].get_cell('col')) == {
        'type': 'checkbox',
        'value': '1',
        'name': 'col',
        'checked': 'checked'
    }
    assert attrs(table.rows[1].get_cell('col')) == {'type': 'checkbox', 'value': '2', 'name': 'col'}


def test_column_is_not_checked_for_non_existing_column():
    class TestTable(tables.Table):
        col = tables.CheckBoxColumn(checked='does_not_exist')

    table = TestTable([
        {'col': '1', 'is_selected': True},
        {'col': '2', 'is_selected': False}
    ])
    assert attrs(table.rows[0].get_cell('col')) == {'type': 'checkbox', 'value': '1', 'name': 'col'}
    assert attrs(table.rows[1].get_cell('col')) == {'type': 'checkbox', 'value': '2', 'name': 'col'}


def test_column_is_alway_checked():
    class TestTable(tables.Table):
        col = tables.CheckBoxColumn(checked=True)

    table = TestTable([
        {'col': 1, 'foo': 'bar'},
        {'col': 2, 'foo': 'baz'}
    ])
    assert attrs(table.rows[0].get_cell('col'))['checked'] == 'checked'
    assert attrs(table.rows[1].get_cell('col'))['checked'] == 'checked'


def test_column_is_checked_callback():
    def is_selected(value, record):
        return value == '1'

    class TestTable(tables.Table):
        col = tables.CheckBoxColumn(attrs={'name': 'col'}, checked=is_selected)

    table = TestTable([{'col': '1'}, {'col': '2'}])
    assert attrs(table.rows[0].get_cell('col')) == {
        'type': 'checkbox',
        'value': '1',
        'name': 'col',
        'checked': 'checked'
    }
    assert attrs(table.rows[1].get_cell('col')) == {'type': 'checkbox', 'value': '2', 'name': 'col'}
