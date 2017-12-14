# coding: utf-8
from itertools import count

from django.db import models
from django.test import SimpleTestCase

import django_tables2 as tables


class RowsTest(SimpleTestCase):
    def test_bound_rows(self):
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

    def test_bound_row(self):
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

        with self.assertRaises(IndexError):
            row.get_cell(3)

        # column name indexing into a row
        assert row.get_cell('name') == record['name']
        assert row.get_cell('occupation') == record['occupation']
        assert row.get_cell('age') == record['age']

        with self.assertRaises(KeyError):
            row.get_cell('gamma')

        # row should support contains check
        assert 'name' in row
        assert 'occupation' in row
        assert 'gamma' not in row

    def test_row_attrs(self):
        '''
        If a callable returns an empty string, do not add a space to the CSS class
        attribute. (#416)
        '''
        counter = count()

        class Table(tables.Table):
            name = tables.Column()

            class Meta(object):
                row_attrs = {
                    'class': lambda: '' if next(counter) % 2 == 0 else 'bla'
                }

        table = Table([
            {'name': 'Brian'},
            {'name': 'Thomas'},
            {'name': 'John'}
        ])

        assert table.rows[0].attrs['class'] == 'even'
        assert table.rows[1].attrs['class'] == 'bla odd'
        assert table.rows[1].attrs['class'] == 'even'

    def test_get_cell_display(self):

        class A(models.Model):
            foo = models.CharField(
                max_length=1,
                choices=(
                    ('a', 'valA'),
                    ('b', 'valB'),
                )
            )

            class Meta:
                app_label = 'tests'

        class B(models.Model):
            a = models.ForeignKey(A, on_delete=models.CASCADE)

            class Meta:
                app_label = 'tests'

        class C(models.Model):
            b = models.ForeignKey(B, on_delete=models.CASCADE)

            class Meta:
                app_label = 'tests'

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

    def test_even_odd_css_class(self):
        '''
        Test for BoundRow.get_even_odd_css_class() method
        '''
        class SimpleTable(tables.Table):
            foo = tables.Column()

            def get_top_pinned_data(self):
                return [{'foo': 'top-pinned'}]

            def get_bottom_pinned_data(self):
                return [{'foo': 'bottom-pinned'}]

        data = [
            {'foo', 'bar'},
            {'foo', 'bas'},
            {'foo', 'baz'},
        ]

        simple_table = SimpleTable(data)

        count = 0
        prev = None
        for row in simple_table.rows:
            if prev:
                assert row.get_even_odd_css_class() != prev.get_even_odd_css_class()
            prev = row
            count += 1

        # count should be 5 because:
        # First row is a top pinned row.
        # Three defaults rows with data.
        # Last row is a bottom pinned row.
        assert count == 5

        # Important!
        # Length of data is five because pinned rows are added to data list.
        # If pinned rows are added only in the iteration on BoundRows,
        # then nothing will display if there are *only* pinned rows
        assert len(simple_table.rows) == 5
