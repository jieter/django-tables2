# coding: utf-8
from attest import assert_hook, raises, Tests
import django_tables2 as tables
from django_tables2 import utils


rows = Tests()


@rows.test
def bound_rows():
    class SimpleTable(tables.Table):
        name = tables.Column()

    data = [
        {'name': 'Bradley'},
        {'name': 'Chris'},
        {'name': 'Peter'},
    ]

    table = SimpleTable(data)

    # iteration
    records = []
    for row in table.rows:
        records.append(row.record)
    assert records == data


@rows.test
def bound_row():
    class SimpleTable(tables.Table):
        name = tables.Column()
        occupation = tables.Column()
        age = tables.Column()

    record = {'name': 'Bradley', 'age': 20, 'occupation': 'programmer'}

    table = SimpleTable([record])
    row = table.rows[0]

    # integer indexing into a row
    assert row[0] == record['name']
    assert row[1] == record['occupation']
    assert row[2] == record['age']

    with raises(IndexError):
        row[3]

    # column name indexing into a row
    assert row['name']       == record['name']
    assert row['occupation'] == record['occupation']
    assert row['age']        == record['age']

    with raises(KeyError):
        row['gamma']
