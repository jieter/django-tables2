# encoding: utf-8
import pytest

import django_tables2 as tables
from django_tables2.rows import BoundRow, BoundRows

from .utils import build_request, parse


class PinnedObj(object):

    def __init__(self, name, age):
        self.name = name
        self.age = age


class SimpleTable(tables.Table):
    name = tables.Column()
    occupation = tables.Column()
    age = tables.Column()

    def get_top_pinned_data(self):
        return [
            PinnedObj("Ron", 90),
            PinnedObj("Jon", 10),
        ]

    def get_bottom_pinned_data(self):
        return [{'occupation': 'Sum age', 'age': 130}]


def test_bound_rows_with_pinned_data():
    record = {'name': 'Grzegorz', 'age': 30, 'occupation': 'programmer'}
    table = SimpleTable([record])
    row = table.rows[0]

    with pytest.raises(IndexError):
        table.rows[1]

    with pytest.raises(IndexError):
        row.get_cell(3)

    assert row.get_cell('name') == record['name']
    assert row.get_cell('occupation') == record['occupation']
    assert row.get_cell('age') == record['age']

    with pytest.raises(KeyError):
        row.get_cell('gamma')

    assert 'name' in row
    assert 'occupation' in row
    assert 'gamma' not in row


def test_as_html():
    '''
    Ensure that html render correctly.
    '''
    request = build_request('/')
    table = SimpleTable([{'name': 'Grzegorz', 'age': 30, 'occupation': 'programmer'}])
    root = parse(table.as_html(request))

    # One row for header
    assert len(root.findall('.//thead/tr')) == 1

    # In the header should be 3 cell.
    assert len(root.findall('.//thead/tr/th')) == 3

    # In the body, should be one original record and 3 pinned rows.
    assert len(root.findall('.//tbody/tr')) == 4
    assert len(root.findall('.//tbody/tr/td')) == 12

    # First top pinned row.
    tr = root.findall('.//tbody/tr')
    td = tr[0].findall('td')
    assert td[0].text == "Ron"
    assert td[1].text == table.default
    assert td[2].text == "90"

    # Second top pinned row.
    td = tr[1].findall('td')
    assert td[0].text == "Jon"
    assert td[1].text == table.default
    assert td[2].text == '10'

    # Original row
    td = tr[2].findall('td')
    assert td[0].text == "Grzegorz"
    assert td[1].text == 'programmer'
    assert td[2].text == '30'

    # First bottom pinned row.
    td = tr[3].findall('td')
    assert td[0].text == table.default
    assert td[1].text == 'Sum age'
    assert td[2].text == '130'


def test_pinned_row_attrs():
    '''
    Testing attrs for pinned rows.
    '''

    pinned_row_attrs = {
        'class': 'super-mega-row',
        'data-foo': 'bar'
    }

    request = build_request('/')
    record = {'name': 'Grzegorz', 'age': 30, 'occupation': 'programmer'}
    table = SimpleTable([record], pinned_row_attrs=pinned_row_attrs)
    html = table.as_html(request)

    assert 'pinned-row' in html
    assert 'super-mega-row' in html
    assert 'data-foo' in html


def test_ordering():
    '''
    Change sorting should not change ordering pinned rows.
    '''
    request = build_request('/')
    records = [
        {'name': 'Alex', 'age': 42, 'occupation': 'programmer'},
        {'name': 'Greg', 'age': 30, 'occupation': 'programmer'},
    ]

    table = SimpleTable(records, order_by='age')
    root = parse(table.as_html(request))
    tr = root.findall('.//tbody/tr')
    assert tr[0].findall('td')[2].text == '90'
    assert tr[1].findall('td')[2].text == '10'
    assert tr[2].findall('td')[2].text == '30'
    assert tr[3].findall('td')[2].text == '42'
    assert tr[4].findall('td')[2].text == '130'

    table = SimpleTable(records, order_by='-age')
    root = parse(table.as_html(request))
    tr = root.findall('.//tbody/tr')
    assert tr[0].findall('td')[2].text == '90'
    assert tr[1].findall('td')[2].text == '10'
    assert tr[2].findall('td')[2].text == '42'
    assert tr[3].findall('td')[2].text == '30'
    assert tr[4].findall('td')[2].text == '130'


def test_bound_rows_getitem():
    '''
    Testing BoundRows.__getitem__() method.
    Checking the return class for simple value and for slice.
    Ensure that inside of BoundRows pinned rows are included in length.
    '''
    records = [
        {'name': 'Greg', 'age': 30, 'occupation': 'policeman'},
        {'name': 'Alex', 'age': 42, 'occupation': 'programmer'},
        {'name': 'John', 'age': 72, 'occupation': 'official'},
    ]

    table = SimpleTable(records, order_by='age')
    assert isinstance(table.rows[0], BoundRow) is True
    assert isinstance(table.rows[0:2], BoundRows) is True
    assert table.rows[0:2][0].get_cell('name') == 'Greg'
    assert len(table.rows[:]) == 6


def test_uniterable_pinned_data():
    '''
    Ensure that, when data for pinned rows are not iterable,
    the ValueError exception will be raised.
    '''
    class FooTable(tables.Table):
        col = tables.Column()

        def get_top_pinned_data(self):
            return 1

    tab = FooTable([1, 2, 3])

    with pytest.raises(ValueError):
        for row in tab.rows:
            pass
