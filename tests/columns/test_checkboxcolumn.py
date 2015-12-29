# coding: utf-8
# pylint: disable=R0912,E0102
from __future__ import unicode_literals

import django_tables2 as tables

from ..utils import attrs, warns


def test_attrs_should_be_translated_for_backwards_compatibility():
    with warns(DeprecationWarning):
        class TestTable(tables.Table):
            col = tables.CheckBoxColumn(header_attrs={"th_key": "th_value"},
                                        attrs={"td_key": "td_value"})

    table = TestTable([{"col": "data"}])
    assert attrs(table.columns["col"].header) == {"type": "checkbox", "th_key": "th_value"}
    assert attrs(table.rows[0]["col"]) == {"type": "checkbox", "td_key": "td_value", "value": "data", "name": "col"}


def new_attrs_should_be_supported():
    with warns(DeprecationWarning):
        class TestTable(tables.Table):
            col1 = tables.CheckBoxColumn(attrs=dict(th__input={"th_key": "th_value"},
                                                     td__input={"td_key": "td_value"}))
            col2 = tables.CheckBoxColumn(attrs=dict(input={"key": "value"}))

    table = TestTable([{"col1": "data", "col2": "data"}])
    assert attrs(table.columns["col1"].header) == {"type": "checkbox", "th_key": "th_value"}
    assert attrs(table.rows[0]["col1"]) == {"type": "checkbox", "td_key": "td_value", "value": "data", "name": "col1"}
    assert attrs(table.columns["col2"].header) == {"type": "checkbox", "key": "value"}
    assert attrs(table.rows[0]["col2"]) == {"type": "checkbox", "key": "value", "value": "data", "name": "col2"}
