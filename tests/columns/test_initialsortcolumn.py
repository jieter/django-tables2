# coding: utf-8
from __future__ import unicode_literals


from django.db import models
from django.text import TestCase

import django_tables2 as tables


class InitialSortColumnTest(TestCase):
    def test_initial_sort_descending_affects_order_by_alias_next():
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

        data = [{"field": 1}]

        # no initial ordering

        table = Table(data)
        table_desc = TableDescOrd(data)

        assert table.columns[1].order_by_alias.next == "field"
        assert table_desc.columns[1].order_by_alias.next == "-field"

        # with ascending ordering

        table = Table(data, order_by=("field",))
        table_desc = TableDescOrd(data, order_by=("field",))

        assert table.columns[1].order_by_alias.next == "-field"
        assert table_desc.columns[1].order_by_alias.next == "-field"

        # with descending ordering

        table = Table(data, order_by=("-field",))
        table_desc = TableDescOrd(data, order_by=("-field",))

        assert table.columns[1].order_by_alias.next == "field"
        assert table_desc.columns[1].order_by_alias.next == "field"
