# coding: utf-8
# pylint: disable=R0912,E0102
from __future__ import unicode_literals
from datetime import date

from django.db import models

import django_tables2 as tables

# Format string: https://docs.djangoproject.com/en/1.4/ref/templates/builtins/#date
# D -- Day of the week, textual, 3 letters  -- 'Fri'
# b -- Month, textual, 3 letters, lowercase -- 'jan'
# Y -- Year, 4 digits.                      -- '1999'

def test_should_handle_explicit_format():
    class TestTable(tables.Table):
        date = tables.DateColumn(format="D b Y")

        class Meta:
            default = "—"

    table = TestTable([{"date": date(2012, 9, 11)},
                       {"date": None}])
    assert table.rows[0]["date"] == "Tue sep 2012"
    assert table.rows[1]["date"] == "—"


def test_should_handle_long_format(settings):
    settings.DATE_FORMAT = "D Y b"

    class TestTable(tables.Table):
        date = tables.DateColumn(short=False)

        class Meta:
            default = "—"

    table = TestTable([{"date": date(2012, 9, 11)},
                       {"date": None}])
    assert table.rows[0]["date"] == "Tue 2012 sep"
    assert table.rows[1]["date"] == "—"


def test_should_handle_short_format(settings):
    settings.SHORT_DATE_FORMAT = "b Y D"

    class TestTable(tables.Table):
        date = tables.DateColumn(short=True)

        class Meta:
            default = "—"

    table = TestTable([{"date": date(2012, 9, 11)},
                       {"date": None}])
    assert table.rows[0]["date"] == "sep 2012 Tue"
    assert table.rows[1]["date"] == "—"


def test_should_be_used_for_datefields():
    class DateModel(models.Model):
        field = models.DateField()

    class Table(tables.Table):
        class Meta:
            model = DateModel

    assert type(Table.base_columns["field"]) == tables.DateColumn
