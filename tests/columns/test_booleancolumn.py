# coding: utf-8
# pylint: disable=R0912,E0102
from __future__ import unicode_literals

from django.db import models

import django_tables2 as tables

from ..utils import attrs


def test_should_be_used_for_booleanfield():
    class BoolModel(models.Model):
        field = models.BooleanField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = BoolModel

    column = Table.base_columns["field"]
    assert type(column) == tables.BooleanColumn
    assert column.empty_values != ()


def test_should_be_used_for_nullbooleanfield():
    class NullBoolModel(models.Model):
        field = models.NullBooleanField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = NullBoolModel

    column = Table.base_columns["field"]
    assert type(column) == tables.BooleanColumn
    assert column.empty_values == ()


def test_treat_none_different_from_false():
    class Table(tables.Table):
        col = tables.BooleanColumn(null=False, default="---")

    table = Table([{"col": None}])
    assert table.rows[0]["col"] == "---"


def test_treat_none_as_false():
    class Table(tables.Table):
        col = tables.BooleanColumn(null=True)

    table = Table([{"col": None}])
    assert table.rows[0]["col"] == '<span class="false">✘</span>'


def test_span_attrs():
    class Table(tables.Table):
        col = tables.BooleanColumn(attrs={"span": {"key": "value"}})

    table = Table([{"col": True}])
    assert attrs(table.rows[0]["col"]) == {"class": "true", "key": "value"}


def test_boolean_field_choices():
    class BoolModel(models.Model):
        field = models.BooleanField(choices=(
            (True, 'yes'),
            (False, 'no')
        ))

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = BoolModel

    table = Table([
        {'field': True},
        {'field': False},
    ])

    assert table.rows[0]['field'] == '<span class="true">✔</span>'
    assert table.rows[1]['field'] == '<span class="false">✘</span>'


def test_boolean_field_choices_with_real_model_instances():
    class BoolModel(models.Model):
        field = models.BooleanField(choices=(
            (True, 'Yes'),
            (False, 'No'))
        )

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = BoolModel

    table = Table(data=[
        BoolModel(field=True),
        BoolModel(field=False)
    ])

    assert table.rows[0]['field'] == '<span class="true">✔</span>'
    assert table.rows[1]['field'] == '<span class="false">✘</span>'
