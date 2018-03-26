# coding: utf-8
from __future__ import unicode_literals

from unittest import skipIf

from django import VERSION as django_version
from django.db import models
from django.test import TestCase

import django_tables2 as tables

from ..app.models import Occupation, Person
from ..utils import attrs, build_request, parse


class BooleanColumnTest(TestCase):
    def test_should_be_used_for_booleanfield(self):
        class BoolModel(models.Model):
            field = models.BooleanField()

            class Meta:
                app_label = 'django_tables2_test'

        class Table(tables.Table):
            class Meta:
                model = BoolModel

        column = Table.base_columns['field']
        self.assertEqual(type(column), tables.BooleanColumn)
        self.assertNotEqual(column.empty_values, ())

    @skipIf(django_version < (2, 1, 0), 'Feature added in django 2.1')
    def test_should_use_nullability_for_booloanfield(self):
        '''
        Django 2.1 supports null=(True|False) for BooleanField.
        '''
        class BoolModel(models.Model):
            field = models.BooleanField(null=True)

            class Meta:
                app_label = 'django_tables2_test'

        class Table(tables.Table):
            class Meta:
                model = BoolModel

        column = Table.base_columns['field']
        self.assertEqual(type(column), tables.BooleanColumn)
        self.assertEqual(column.empty_values, ())

    def test_should_be_used_for_nullbooleanfield(self):
        class NullBoolModel(models.Model):
            field = models.NullBooleanField()

            class Meta:
                app_label = 'django_tables2_test'

        class Table(tables.Table):
            class Meta:
                model = NullBoolModel

        column = Table.base_columns['field']
        self.assertEqual(type(column), tables.BooleanColumn)
        self.assertEqual(column.empty_values, ())

    def test_treat_none_different_from_false(self):
        class Table(tables.Table):
            col = tables.BooleanColumn(null=False, default='---')

        table = Table([{'col': None}])
        self.assertEqual(table.rows[0].get_cell('col'), '---')

    def test_treat_none_as_false(self):
        class Table(tables.Table):
            col = tables.BooleanColumn(null=True)

        table = Table([{'col': None}])
        self.assertEqual(table.rows[0].get_cell('col'), '<span class="false">✘</span>')

    def test_value_returns_a_raw_value_without_html(self):
        class Table(tables.Table):
            col = tables.BooleanColumn()

        table = Table([{'col': True}, {'col': False}])
        self.assertEqual(table.rows[0].get_cell_value('col'), 'True')
        self.assertEqual(table.rows[1].get_cell_value('col'), 'False')

    def test_span_attrs(self):
        class Table(tables.Table):
            col = tables.BooleanColumn(attrs={'span': {'key': 'value'}})

        table = Table([{'col': True}])
        self.assertEqual(attrs(table.rows[0].get_cell('col')), {'class': 'true', 'key': 'value'})

    def test_boolean_field_choices_with_real_model_instances(self):
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

        self.assertEqual(table.rows[0].get_cell('field'), '<span class="true">✔</span>')
        self.assertEqual(table.rows[1].get_cell('field'), '<span class="false">✘</span>')

    def test_boolean_field_choices_spanning_relations(self):
        'The inverse lookup voor boolean choices should also work on related models'

        class Table(tables.Table):
            boolean = tables.BooleanColumn(accessor='occupation.boolean_with_choices')

            class Meta:
                model = Person

        model_true = Occupation.objects.create(
            name='true-name',
            boolean_with_choices=True
        )
        model_false = Occupation.objects.create(
            name='false-name',
            boolean_with_choices=False
        )

        table = Table([
            Person(first_name='True', last_name='False', occupation=model_true),
            Person(first_name='True', last_name='False', occupation=model_false)
        ])

        self.assertEqual(table.rows[0].get_cell('boolean'), '<span class="true">✔</span>')
        self.assertEqual(table.rows[1].get_cell('boolean'), '<span class="false">✘</span>')

    def test_boolean_should_not_prevent_rendering_of_other_columns(self):
        '''Test for issue 360'''
        class Table(tables.Table):
            boolean = tables.BooleanColumn(yesno='waar,onwaar')

            class Meta:
                model = Occupation
                fields = ('boolean', 'name')

        Occupation.objects.create(name='Waar', boolean=True),
        Occupation.objects.create(name='Onwaar', boolean=False),
        Occupation.objects.create(name='Onduidelijk')

        html = Table(Occupation.objects.all()).as_html(build_request())
        root = parse(html)

        self.assertEqual(root.findall('.//tbody/tr[1]/td')[1].text, 'Waar')
        self.assertEqual(root.findall('.//tbody/tr[2]/td')[1].text, 'Onwaar')
