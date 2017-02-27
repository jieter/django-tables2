# coding: utf-8
import django_tables2 as tables
import pytest
from django.db import models


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


def test_row_attrs():
    '''
    If a callable returns an empty string, do not add a space to the CSS class
    attribute. (#416)
    '''
    from itertools import count
    counter = count()

    class Table(tables.Table):
        name = tables.Column()

        class Meta(object):
            row_attrs = {
                'class': lambda x: '' if next(counter) % 2 == 0 else 'bla'
            }

    table = Table([
        {'name': 'Brian'},
        {'name': 'Thomas'},
        {'name': 'John'}
    ])

    assert table.rows[0].attrs['class'] == 'even'
    assert table.rows[1].attrs['class'] == 'bla odd'
    assert table.rows[1].attrs['class'] == 'even'


def test_get_cell_display():

    class A(models.Model):
        foo = models.CharField(
            max_length=1,
            choices=(
                ('a', 'valA'),
                ('b', 'valB'),
            )
        )

        class Meta:
            app_label = 'django_tables2_test'

    class B(models.Model):
        a = models.ForeignKey(A, on_delete=models.CASCADE)

        class Meta:
            app_label = 'django_tables2_test'

    class C(models.Model):
        b = models.ForeignKey(B, on_delete=models.CASCADE)

        class Meta:
            app_label = 'django_tables2_test'

    class Tab(tables.Table):
        a = tables.Column(accessor="b.a.foo")

        class Meta:
            model = C

    a = A(foo='a')
    b = B(a=a)
    c = C(b=b)

    tab = Tab([c])
    row = tab.rows[0]
    assert row.get_cell('a') == 'valA'
