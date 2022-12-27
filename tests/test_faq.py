from django.test import SimpleTestCase

import django_tables2 as tables

from .utils import build_request, parse

TEST_DATA = [
    {"name": "Belgium", "population": 11200000},
    {"name": "Luxembourgh", "population": 540000},
    {"name": "France", "population": 66000000},
]


class FaqTest(SimpleTestCase):
    def test_row_counter_using_templateColumn(self):
        class CountryTable(tables.Table):
            counter = tables.TemplateColumn("{{ row_counter }}")
            name = tables.Column()

        expected = "<td >0</td>"

        table = CountryTable(TEST_DATA)
        html = table.as_html(build_request())
        self.assertIn(expected, html)

        # the counter should start at zero the second time too
        table = CountryTable(TEST_DATA)
        html = table.as_html(build_request())
        self.assertIn(expected, html)

    def test_row_footer_total(self):
        class CountryTable(tables.Table):
            name = tables.Column()
            population = tables.Column(
                footer=lambda table: f'Total: {sum(x["population"] for x in table.data)}'
            )

        table = CountryTable(TEST_DATA)
        html = table.as_html(build_request())

        columns = parse(html).findall(".//tfoot/tr")[-1].findall("td")
        self.assertEqual(columns[1].text, "Total: 77740000")
