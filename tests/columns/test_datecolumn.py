from datetime import date

from django.db import models
from django.test import SimpleTestCase

import django_tables2 as tables


def isoformat_link(value):
    return f"/test/{value.isoformat()}/"


class DateColumnTest(SimpleTestCase):
    """
    Date formatting test case.

    Format string: https://docs.djangoproject.com/en/stable/ref/templates/builtins/#date
    D -- Day of the week, textual, 3 letters  -- 'Fri'
    b -- Month, textual, 3 letters, lowercase -- 'jan'
    Y -- Year, 4 digits.                      -- '1999'
    """

    def test_should_handle_explicit_format(self):
        class TestTable(tables.Table):
            date = tables.DateColumn(format="D b Y")
            date_linkify = tables.DateColumn(
                accessor="date", format="D b Y", linkify=isoformat_link
            )

            class Meta:
                default = "—"

        table = TestTable([{"date": date(2012, 9, 11)}, {"date": None}])
        self.assertEqual(table.rows[0].get_cell("date"), "Tue sep 2012")
        self.assertEqual(
            table.rows[0].get_cell("date_linkify"), '<a href="/test/2012-09-11/">Tue sep 2012</a>'
        )
        self.assertEqual(table.rows[1].get_cell("date"), "—")

    def test_should_handle_long_format(self):
        class TestTable(tables.Table):
            date = tables.DateColumn(short=False)

            class Meta:
                default = "—"

        table = TestTable([{"date": date(2012, 9, 11)}, {"date": None}])
        self.assertEqual(table.rows[0].get_cell("date"), "Sept. 11, 2012")
        self.assertEqual(table.rows[1].get_cell("date"), "—")

    def test_should_handle_short_format(self):
        class TestTable(tables.Table):
            date = tables.DateColumn(short=True)

            class Meta:
                default = "—"

        table = TestTable([{"date": date(2012, 9, 11)}, {"date": None}])
        self.assertEqual(table.rows[0].get_cell("date"), "09/11/2012")
        self.assertEqual(table.rows[1].get_cell("date"), "—")

    def test_should_be_used_for_datefields(self):
        class DateModel(models.Model):
            field = models.DateField()

            class Meta:
                app_label = "django_tables2_test"

        class Table(tables.Table):
            class Meta:
                model = DateModel

        self.assertEqual(type(Table.base_columns["field"]), tables.DateColumn)

    def test_value_returns_a_raw_value_without_html(self):
        class Table(tables.Table):
            date = tables.DateColumn()
            date_linkify = tables.DateColumn(accessor="date", linkify=isoformat_link)

        table = Table([{"date": date(2012, 9, 12)}])
        self.assertEqual(table.rows[0].get_cell_value("date"), "09/12/2012")
        self.assertEqual(
            table.rows[0].get_cell("date_linkify"), '<a href="/test/2012-09-12/">09/12/2012</a>'
        )
