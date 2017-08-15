# coding: utf-8
from __future__ import unicode_literals

from datetime import datetime

import pytest
import pytz
from django.db import models

import django_tables2 as tables


'''
Format string: https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date
D -- Day of the week, textual, 3 letters  -- 'Fri'
b -- Month, textual, 3 letters, lowercase -- 'jan'
Y -- Year, 4 digits.                      -- '1999'
A -- 'AM' or 'PM'.                        -- 'AM'
f -- Time, in 12-hour hours[:minutes]     -- '1', '1:30'
'''


@pytest.yield_fixture
def dt():
    dt = datetime(2012, 9, 11, 12, 30, 0)
    yield pytz.timezone('Australia/Brisbane').localize(dt)


def test_should_handle_explicit_format(dt):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(format='D b Y')

        class Meta:
            default = '—'

    table = TestTable([{'date': dt}, {'date': None}])
    assert table.rows[0].get_cell('date') == 'Tue sep 2012'
    assert table.rows[1].get_cell('date') == '—'


def test_should_handle_long_format(dt, settings):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(short=False)

        class Meta:
            default = '—'

    settings.DATETIME_FORMAT = 'D Y b A f'
    table = TestTable([{'date': dt}, {'date': None}])
    assert table.rows[0].get_cell('date') == 'Tue 2012 sep PM 12:30'
    assert table.rows[1].get_cell('date') == '—'


def test_should_handle_short_format(dt, settings):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(short=True)

        class Meta:
            default = '—'

    settings.SHORT_DATETIME_FORMAT = 'b Y D A f'
    table = TestTable([{'date': dt}, {'date': None}])
    assert table.rows[0].get_cell('date') == 'sep 2012 Tue PM 12:30'
    assert table.rows[1].get_cell('date') == '—'


def test_should_be_used_for_datetimefields():
    class DateTimeModel(models.Model):
        field = models.DateTimeField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = DateTimeModel

    assert type(Table.base_columns['field']) == tables.DateTimeColumn


def test_value_returns_a_raw_value_without_html(dt, settings):
    settings.SHORT_DATETIME_FORMAT = 'b Y D A f'

    class Table(tables.Table):
        col = tables.DateTimeColumn()

    table = Table([{'col': dt}])
    assert table.rows[0].get_cell_value('col') == 'sep 2012 Tue PM 12:30'
