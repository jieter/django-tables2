# coding: utf-8
from __future__ import absolute_import, unicode_literals

import django_tables2 as tables


def test_dynamically_adding_columns():
    '''
    When adding columns to self.base_columns, they are actually added to
    the class attribute `Table.base_columns`, and not to the instance
    attribute, `table.base_columns`

    issue #403
    '''
    data = [
        {'name': 'Adrian', 'country': 'Australia'},
        {'name': 'Adrian', 'country': 'Brazil'},
        {'name': 'Audrey', 'country': 'Chile'},
        {'name': 'Bassie', 'country': 'Belgium'},
    ]

    class MyTable(tables.Table):
        name = tables.Column()

    # this is obvious:
    assert list(MyTable(data).columns.columns.keys()) == ['name']

    assert list(MyTable(data, extra_columns=[
        ('country', tables.Column())
    ]).columns.columns.keys()) == ['name', 'country']

    # this new instance should not have the extra columns added to the first instance.
    assert list(MyTable(data).columns.columns.keys()) == ['name']
