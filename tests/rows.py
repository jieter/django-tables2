# -*- coding: utf-8 -*-
"""Test the core table functionality."""
from attest import Tests, Assert
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
    Assert(records) == data


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
    Assert(row[0]) == record['name']
    Assert(row[1]) == record['occupation']
    Assert(row[2]) == record['age']

    with Assert.raises(IndexError) as error:
        row[3]

    # column name indexing into a row
    Assert(row['name'])       == record['name']
    Assert(row['occupation']) == record['occupation']
    Assert(row['age'])        == record['age']

    with Assert.raises(KeyError) as error:
        row['gamma']
