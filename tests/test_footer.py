# coding: utf-8
from bs4 import BeautifulSoup

import django_tables2 as tables

from .utils import build_request

MEMORY_DATA = [
    {'name': 'Queensland', 'country': 'Australia', 'population': 4750500},
    {'name': 'New South Wales', 'country': 'Australia', 'population': 7565500},
    {'name': 'Victoria', 'country': 'Australia', 'population': 6000000},
    {'name': 'Tasmania', 'country': 'Australia', 'population': 517000}
]


def test_has_footer_is_False_without_footer():
    class Table(tables.Table):
        name = tables.Column()
        country = tables.Column()
        population = tables.Column()

    table = Table(MEMORY_DATA)
    assert table.has_footer() is False


def test_footer():
    class Table(tables.Table):
        name = tables.Column()
        country = tables.Column(footer='Total:')
        population = tables.Column(
            footer=lambda table: sum(x['population'] for x in table.data)
        )

    table = Table(MEMORY_DATA)
    assert table.has_footer() is True

    html = table.as_html(build_request('/'))

    soup = BeautifulSoup(html, "lxml")
    row = soup.find("tfoot").tr
    columns = row.find_all("td")

    assert columns[1].text == "Total:"
    assert columns[2].text == "18833000"


def test_footer_disable_on_table():
    '''
    Showing the footer can be disabled using show_footer argument to the Table
    constructor
    '''
    class Table(tables.Table):
        name = tables.Column()
        country = tables.Column(footer='Total:')

    table = Table(MEMORY_DATA, show_footer=False)
    assert table.has_footer() is False


class SummingColumn(tables.Column):
    def render_footer(self, bound_column, table):
        return sum(bound_column.accessor.resolve(row) for row in table.data)


class TestTable(tables.Table):
    name = tables.Column()
    country = tables.Column(footer='Total:')
    population = SummingColumn()


def test_footer_column_method():
    table = TestTable(MEMORY_DATA)
    html = table.as_html(build_request('/'))

    soup = BeautifulSoup(html, "lxml")
    row = soup.find("tfoot").tr
    columns = row.find_all("td")

    assert columns[1].text == "Total:"
    assert columns[2].text == "18833000"
