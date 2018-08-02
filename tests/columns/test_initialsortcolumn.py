# coding: utf-8
from __future__ import unicode_literals

from django.db import models
from django.test import TestCase

import django_tables2 as tables


class InitialSortColumnTest(TestCase):
    def test_initial_sort_descending_affects_order_by_alias_next(self):
        class IntModel(models.Model):
            field = models.IntegerField()

            class Meta:
                app_label = "django_tables2_test"

        class Table(tables.Table):
            class Meta:
                model = IntModel

        class TableDescOrd(tables.Table):
            field = tables.Column(initial_sort_descending=True)

            class Meta:
                model = IntModel

        data = [
            {"field": 1},
            {"field": 5},
            {"field": 3},
        ]

        # no initial ordering

        table = Table(data)
        table_desc = TableDescOrd(data)

        self.assertEqual(table.columns[1].order_by_alias.next, "field")
        self.assertEqual(table_desc.columns[1].order_by_alias.next, "-field")

        # with ascending ordering

        table = Table(data, order_by=("field",))
        table_desc = TableDescOrd(data, order_by=("field",))

        self.assertEqual(table.columns[1].order_by_alias.next, "-field")
        self.assertEqual(table_desc.columns[1].order_by_alias.next, "-field")
        self.assertEqual(table.rows[0].get_cell("field"), 1)
        self.assertEqual(table.rows[1].get_cell("field"), 3)
        self.assertEqual(table.rows[2].get_cell("field"), 5)
        self.assertEqual(table_desc.rows[0].get_cell("field"), 1)
        self.assertEqual(table_desc.rows[1].get_cell("field"), 3)
        self.assertEqual(table_desc.rows[2].get_cell("field"), 5)

        # with descending ordering

        table = Table(data, order_by=("-field",))
        table_desc = TableDescOrd(data, order_by=("-field",))

        self.assertEqual(table.columns[1].order_by_alias.next, "field")
        self.assertEqual(table_desc.columns[1].order_by_alias.next, "field")
        self.assertEqual(table.rows[0].get_cell("field"), 5)
        self.assertEqual(table.rows[1].get_cell("field"), 3)
        self.assertEqual(table.rows[2].get_cell("field"), 1)
        self.assertEqual(table_desc.rows[0].get_cell("field"), 5)
        self.assertEqual(table_desc.rows[1].get_cell("field"), 3)
        self.assertEqual(table_desc.rows[2].get_cell("field"), 1)
