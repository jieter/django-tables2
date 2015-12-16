# coding: utf-8
# pylint: disable=R0912,E0102
from __future__ import unicode_literals

from datetime import datetime

import pytz
from django.db import models

import django_tables2 as tables
import pytest

try:
    from django.utils import timezone
except ImportError:
    timezone = None

# Format string: https://docs.djangoproject.com/en/1.4/ref/templates/builtins/#date
# D -- Day of the week, textual, 3 letters  -- 'Fri'
# b -- Month, textual, 3 letters, lowercase -- 'jan'
# Y -- Year, 4 digits.                      -- '1999'
# A -- 'AM' or 'PM'.                        -- 'AM'
# f -- Time, in 12-hour hours[:minutes]     -- '1', '1:30'

@pytest.yield_fixture
def dt():
    dt = datetime(2012, 9, 11, 12, 30, 0)
    if timezone:
        # If the version of Django has timezone support, convert from naive to
        # UTC, the test project uses Australia/Brisbane so regardless the
        # output from the column should be the same.
        dt = pytz.timezone("Australia/Brisbane").localize(dt)
    yield dt


def test_should_handle_explicit_format(dt):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(format="D b Y")

        class Meta:
            default = "—"

    table = TestTable([{"date": dt}, {"date": None}])
    assert table.rows[0]["date"] == "Tue sep 2012"
    assert table.rows[1]["date"] == "—"


def test_should_handle_long_format(dt, settings):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(short=False)

        class Meta:
            default = "—"

    settings.DATETIME_FORMAT = "D Y b A f"
    table = TestTable([{"date": dt}, {"date": None}])
    assert table.rows[0]["date"] == "Tue 2012 sep PM 12:30"
    assert table.rows[1]["date"] == "—"


def test_should_handle_short_format(dt, settings):
    class TestTable(tables.Table):
        date = tables.DateTimeColumn(short=True)

        class Meta:
            default = "—"

    settings.SHORT_DATETIME_FORMAT = "b Y D A f"
    table = TestTable([{"date": dt}, {"date": None}])
    assert table.rows[0]["date"] == "sep 2012 Tue PM 12:30"
    assert table.rows[1]["date"] == "—"


def test_should_be_used_for_datetimefields():
    class DateTimeModel(models.Model):
        field = models.DateTimeField()
        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = DateTimeModel

    assert type(Table.base_columns["field"]) == tables.DateTimeColumn
