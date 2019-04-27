from django.db import models
from django.test import SimpleTestCase

import django_tables2 as tables

MEMORY_DATA = [
    {"url": "http://example.com", "name": "Example"},
    {"url": "https://example.com", "name": "Example (https)"},
    {"url": "ftp://example.com", "name": "Example (ftp)"},
]


class UrlColumnTest(SimpleTestCase):
    def test_should_turn_url_into_hyperlink(self):
        class TestTable(tables.Table):
            url = tables.URLColumn()

        table = TestTable(MEMORY_DATA)

        self.assertEqual(
            table.rows[0].get_cell("url"), '<a href="http://example.com">http://example.com</a>'
        )
        self.assertEqual(
            table.rows[1].get_cell("url"), '<a href="https://example.com">https://example.com</a>'
        )

    def test_should_be_used_for_urlfields(self):
        class URLModel(models.Model):
            field = models.URLField()

            class Meta:
                app_label = "django_tables2_test"

        class Table(tables.Table):
            class Meta:
                model = URLModel

        assert type(Table.base_columns["field"]) == tables.URLColumn

    def test_text_can_be_overridden(self):
        class Table(tables.Table):
            url = tables.URLColumn(text="link")

        table = Table(MEMORY_DATA)

        assert table.rows[0].get_cell("url") == '<a href="http://example.com">link</a>'

    def test_text_can_be_overridden_with_callable(self):
        class Table(tables.Table):
            url = tables.URLColumn(text=lambda record: record["name"])

        table = Table(MEMORY_DATA)

        assert table.rows[0].get_cell("url") == '<a href="http://example.com">Example</a>'
        assert table.rows[1].get_cell("url") == '<a href="https://example.com">Example (https)</a>'

    def test_value_returns_a_raw_value_without_html(self):
        class TestTable(tables.Table):
            col = tables.URLColumn()

        table = TestTable([{"col": "http://example.com"}])

        assert table.rows[0].get_cell_value("col") == "http://example.com"
