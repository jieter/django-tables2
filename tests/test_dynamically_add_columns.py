# coding: utf-8
from __future__ import absolute_import, unicode_literals

import django_tables2 as tables

import pytest

@pytest.mark.skip('not yet fixed, issue #403')
def test_dynamically_adding_columns():
    class Table(tables.Table):
        '''
        This table allows adding columns while initializing the table.
        '''
        name = tables.Column()

        def __init__(self, data, extra_columns=None, *args, **kwargs):
            '''
            Pass in a list of tuples of extra columns to add in the
            format (colunm_name, column)
            '''
            if extra_columns:
                for col_name, col in extra_columns:
                    self.base_columns[col_name] = col
            super(Table, self).__init__(data, *args, **kwargs)

    data = [
        {'name': 'Adrian', 'country': 'Australia'},
        {'name': 'Adrian', 'country': 'Brazil'},
        {'name': 'Audrey', 'country': 'Chile'},
        {'name': 'Bassie', 'country': 'Belgium'},
    ]
    table = Table(data, extra_columns=[('country', tables.Column())])
    assert table.columns.columns.keys() == ['name', 'country']

    # a new instance should not have the extra columns added to the
    # first instance.
    table2 = Table(data)
    assert table2.columns.columns.keys() == ['name']
