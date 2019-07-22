from datetime import datetime

import pytz
from django.db import models
from django.test import SimpleTestCase, override_settings

import django_tables2 as tables


def isoformat_link(value):
    return "/test/{}/".format(value.isoformat())


class DateTimeColumnTest(SimpleTestCase):
    """
    Format string: https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date
    D -- Day of the week, textual, 3 letters  -- 'Fri'
    b -- Month, textual, 3 letters, lowercase -- 'jan'
    Y -- Year, 4 digits.                      -- '1999'
    A -- 'AM' or 'PM'.                        -- 'AM'
    f -- Time, in 12-hour hours[:minutes]     -- '1', '1:30'
    """

    def dt(self):
        dt = datetime(2012, 9, 11, 12, 30, 0)
        return pytz.timezone("Australia/Brisbane").localize(dt)

    def test_should_handle_explicit_format(self):
        class TestTable(tables.Table):
            date = tables.DateTimeColumn(format="D b Y")
            date_linkify = tables.DateTimeColumn(
                format="D b Y", accessor="date", linkify=isoformat_link
            )

            class Meta:
                default = "—"

        table = TestTable([{"date": self.dt()}, {"date": None}])
        assert table.rows[0].get_cell("date") == "Tue sep 2012"
        self.assertEqual(
            table.rows[0].get_cell("date_linkify"),
            '<a href="/test/2012-09-11T12:30:00+10:00/">Tue sep 2012</a>',
        )
        assert table.rows[1].get_cell("date") == "—"

    @override_settings(DATETIME_FORMAT="D Y b A f")
    def test_should_handle_long_format(self):
        class TestTable(tables.Table):
            date = tables.DateTimeColumn(short=False)

            class Meta:
                default = "—"

        table = TestTable([{"date": self.dt()}, {"date": None}])
        assert table.rows[0].get_cell("date") == "Tue 2012 sep PM 12:30"
        assert table.rows[1].get_cell("date") == "—"

    @override_settings(SHORT_DATETIME_FORMAT="b Y D A f")
    def test_should_handle_short_format(self):
        class TestTable(tables.Table):
            date = tables.DateTimeColumn(short=True)

            class Meta:
                default = "—"

        table = TestTable([{"date": self.dt()}, {"date": None}])
        assert table.rows[0].get_cell("date") == "sep 2012 Tue PM 12:30"
        assert table.rows[1].get_cell("date") == "—"

    def test_should_be_used_for_datetimefields(self):
        class DateTimeModel(models.Model):
            field = models.DateTimeField()

            class Meta:
                app_label = "django_tables2_test"

        class Table(tables.Table):
            class Meta:
                model = DateTimeModel

        assert type(Table.base_columns["field"]) == tables.DateTimeColumn

    @override_settings(SHORT_DATETIME_FORMAT="b Y D A f")
    def test_value_returns_a_raw_value_without_html(self):
        class Table(tables.Table):
            col = tables.DateTimeColumn()

        table = Table([{"col": self.dt()}])
        assert table.rows[0].get_cell_value("col") == "sep 2012 Tue PM 12:30"
