# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.db import models

import django_tables2 as tables

try:
    from django.contrib.postgres.fields import HStoreField, JSONField
    JSONFIELD_AVAILABLE = True
except ImportError:
    # fields are introduced in django == 1.9
    # remove shim wen we drop support for django 1.8
    JSONFIELD_AVAILABLE = False


@pytest.mark.skipif(not JSONFIELD_AVAILABLE, reason='JSONField added in django 1.9')
def test_should_be_used_for_json_and_hstore_fields():
    class Model(models.Model):
        json = JSONField()
        hstore = HStoreField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = Model

    assert isinstance(Table.base_columns['json'], tables.JSONColumn)
    assert isinstance(Table.base_columns['hstore'], tables.JSONColumn)


def test_jsoncolumn_dict():
    column = tables.JSONColumn()

    record = {'json': {'species': 'Falcon'}}
    html = column.render(value=record['json'], record=record)
    assert html == '<pre >{\n  &quot;species&quot;: &quot;Falcon&quot;\n}</pre>'


def test_jsoncolumn_string():
    column = tables.JSONColumn()

    record = {'json': "really?"}
    html = column.render(value=record['json'], record=record)
    assert html == '<pre >&quot;really?&quot;</pre>'


def test_jsoncolumn_number():
    column = tables.JSONColumn()

    record = {'json': 3.14}
    html = column.render(value=record['json'], record=record)
    assert html == '<pre >3.14</pre>'
