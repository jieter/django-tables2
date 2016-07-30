# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.db import models

import django_tables2 as tables

from ..app.models import Occupation, Person
from ..utils import attrs


def test_should_be_used_for_booleanfield():
    class BoolModel(models.Model):
        field = models.BooleanField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = BoolModel

    column = Table.base_columns['field']
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

    column = Table.base_columns['field']
    assert type(column) == tables.BooleanColumn
    assert column.empty_values == ()


def test_treat_none_different_from_false():
    class Table(tables.Table):
        col = tables.BooleanColumn(null=False, default='---')

    table = Table([{'col': None}])
    assert table.rows[0].get_cell('col') == '---'


def test_treat_none_as_false():
    class Table(tables.Table):
        col = tables.BooleanColumn(null=True)

    table = Table([{'col': None}])
    assert table.rows[0].get_cell('col') == '<span class="false">✘</span>'


def test_span_attrs():
    class Table(tables.Table):
        col = tables.BooleanColumn(attrs={'span': {'key': 'value'}})

    table = Table([{'col': True}])
    assert attrs(table.rows[0].get_cell('col')) == {'class': 'true', 'key': 'value'}


def test_boolean_field_choices_with_real_model_instances():
    '''
    If a booleanField has choices defined, the value argument passed to
    BooleanColumn.render() is the rendered value, not a bool.
    '''
    class BoolModelChoices(models.Model):
        field = models.BooleanField(choices=(
            (True, 'Yes'),
            (False, 'No'))
        )

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = BoolModelChoices

    table = Table([BoolModelChoices(field=True), BoolModelChoices(field=False)])

    assert table.rows[0].get_cell('field') == '<span class="true">✔</span>'
    assert table.rows[1].get_cell('field') == '<span class="false">✘</span>'


@pytest.mark.django_db
def test_boolean_field_choices_spanning_relations():
    'The inverse lookup voor boolean choices should also work on related models'

    class Table(tables.Table):
        boolean = tables.BooleanColumn(accessor='occupation.boolean')

        class Meta:
            model = Person

    model_true = Occupation.objects.create(name='true-name', boolean=True)
    model_false = Occupation.objects.create(name='false-name', boolean=False)

    table = Table([
        Person(first_name='True', last_name='False', occupation=model_true),
        Person(first_name='True', last_name='False', occupation=model_false)
    ])

    assert table.rows[0].get_cell('boolean') == '<span class="true">✔</span>'
    assert table.rows[1].get_cell('boolean') == '<span class="false">✘</span>'
