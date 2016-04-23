# coding: utf-8
import pytest

import django_tables2 as tables


def test_bound_rows():
    class SimpleTable(tables.Table):
        name = tables.Column()

    data = [
        {'name': 'Bradley'},
        {'name': 'Chris'},
        {'name': 'Davina'},
    ]

    table = SimpleTable(data)

    # iteration
    records = []
    for row in table.rows:
        records.append(row.record)
    assert records == data


def test_bound_row():
    class SimpleTable(tables.Table):
        name = tables.Column()
        occupation = tables.Column()
        age = tables.Column()

    record = {'name': 'Bradley', 'age': 20, 'occupation': 'programmer'}

    table = SimpleTable([record])
    row = table.rows[0]

    # integer indexing into a row
    assert row.get_cell(0) == record['name']
    assert row.get_cell(1) == record['occupation']
    assert row.get_cell(2) == record['age']

    with pytest.raises(IndexError):
        row.get_cell(3)

    # column name indexing into a row
    assert row.get_cell('name') == record['name']
    assert row.get_cell('occupation') == record['occupation']
    assert row.get_cell('age') == record['age']

    with pytest.raises(KeyError):
        row.get_cell('gamma')

    # row should support contains check
    assert 'name' in row
    assert 'occupation' in row
    assert 'gamma' not in row
