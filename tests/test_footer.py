from django.test import SimpleTestCase

import django_tables2 as tables

from .utils import build_request, parse

MEMORY_DATA = [
    {"name": "Queensland", "country": "Australia", "population": 4750500},
    {"name": "New South Wales", "country": "Australia", "population": 7565500},
    {"name": "Victoria", "country": "Australia", "population": 6000000},
    {"name": "Tasmania", "country": "Australia", "population": 517000},
]


class FooterTest(SimpleTestCase):
    def test_has_footer_is_False_without_footer(self):
        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column()
            population = tables.Column()

        table = Table(MEMORY_DATA)
        self.assertFalse(table.has_footer())

    def test_footer(self):
        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column(footer="Total:")
            population = tables.Column(
                footer=lambda table: sum(x["population"] for x in table.data)
            )

        table = Table(MEMORY_DATA)
        self.assertTrue(table.has_footer())
        html = table.as_html(build_request("/"))

        columns = parse(html).findall(".//tfoot/tr/td")
        self.assertEqual(columns[1].text, "Total:")
        self.assertEqual(columns[2].text, "18833000")

    def test_footer_disable_on_table(self):
        """
        Showing the footer can be disabled using show_footer argument to the Table
        constructor
        """

        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column(footer="Total:")

        table = Table(MEMORY_DATA, show_footer=False)
        self.assertFalse(table.has_footer())

    def test_footer_column_method(self):
        class SummingColumn(tables.Column):
            def render_footer(self, bound_column, table):
                return sum(bound_column.accessor.resolve(row) for row in table.data)

        class TestTable(tables.Table):
            name = tables.Column()
            country = tables.Column(footer="Total:")
            population = SummingColumn()

        table = TestTable(MEMORY_DATA)
        html = table.as_html(build_request("/"))

        columns = parse(html).findall(".//tfoot/tr/td")
        self.assertEqual(columns[1].text, "Total:")
        self.assertEqual(columns[2].text, "18833000")

    def test_footer_has_class(self):
        class SummingColumn(tables.Column):
            def render_footer(self, bound_column, table):
                return sum(bound_column.accessor.resolve(row) for row in table.data)

        class TestTable(tables.Table):
            name = tables.Column()
            country = tables.Column(footer="Total:")
            population = SummingColumn(attrs={"tf": {"class": "population_sum"}})

        table = TestTable(MEMORY_DATA)
        html = table.as_html(build_request("/"))

        columns = parse(html).findall(".//tfoot/tr/td")
        self.assertEqual(columns[2].attrib, {"class": "population_sum"})

    def test_footer_custom_attriubtes(self):
        class SummingColumn(tables.Column):
            def render_footer(self, bound_column, table):
                return sum(bound_column.accessor.resolve(row) for row in table.data)

        class TestTable(tables.Table):
            name = tables.Column()
            country = tables.Column(footer="Total:", attrs={"tf": {"align": "right"}})
            population = SummingColumn()

        table = TestTable(MEMORY_DATA)
        table.columns["country"].attrs["tf"] = {"align": "right"}
        html = table.as_html(build_request("/"))

        columns = parse(html).findall(".//tfoot/tr/td")
        assert "align" in columns[1].attrib
