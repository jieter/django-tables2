# coding: utf-8
from __future__ import unicode_literals

from datetime import time

from django.db import models

import django_tables2 as tables


# Format string: https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date


def test_should_handle_explicit_format():
    class TestTable(tables.Table):
        time = tables.TimeColumn(format='H:i:s')

        class Meta:
            default = '—'

    table = TestTable([{'time': time(11, 11, 11)},
                       {'time': None}])
    assert table.rows[0].get_cell('time') == "11:11:11"
    assert table.rows[1].get_cell('time') == "—"


def test_should_be_used_for_timefields():
    class TimeModel(models.Model):
        field = models.TimeField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = TimeModel

    assert type(Table.base_columns['field']) == tables.TimeColumn


def test_value_returns_a_raw_value_without_html():
    class Table(tables.Table):
        col = tables.TimeColumn(format='H:i:s')

    table = Table([{'col': time(11, 11, 11)}])
    assert table.rows[0].get_cell_value('col') == '11:11:11'
