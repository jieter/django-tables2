# coding: utf-8
from __future__ import unicode_literals

from django.test import TestCase

from django_tables2 import Table
from django_tables2.data import TableData, TableListData, TableQuerysetData

from .app.models import Person


class TableDataFactoryTest(TestCase):
    def test_invalid_data_None(self):
        with self.assertRaises(ValueError):
            TableData.from_data(None)

    def test_invalid_data_int(self):
        with self.assertRaises(ValueError):
            TableData.from_data(1)

    def test_invalid_data_classes(self):
        class Klass(object):
            pass

        with self.assertRaises(ValueError):
            TableData.from_data(Klass())

        class Bad(object):
            def __len__(self):
                pass

        with self.assertRaises(ValueError):
            TableData.from_data(Bad())

    def test_valid_QuerySet(self):
        data = TableData.from_data(Person.objects.all())
        assert isinstance(data, TableQuerysetData)

    def test_valid_list_of_dicts(self):
        data = TableData.from_data([{'name': 'John'}, {'name': 'Pete'}])
        assert isinstance(data, TableListData)
        assert len(data) == 2

    def test_valid_tuple_of_dicts(self):
        data = TableData.from_data(({'name': 'John'}, {'name': 'Pete'}))
        assert isinstance(data, TableListData)
        assert len(data) == 2

    def test_valid_class(self):
        class Datasource(object):
            def __len__(self):
                return 1

            def __getitem__(self, pos):
                if pos != 0:
                    raise IndexError()
                return {'a': 1}

        data = TableData.from_data(Datasource())
        assert len(data) == 1


class TableDataTest(TestCase):
    def test_knows_its_default_name(self):
        data = TableData.from_data([{}])
        assert data.verbose_name == 'item'
        assert data.verbose_name_plural == 'items'

    def test_knows_its_name(self):
        data = TableData.from_data(Person.objects.all())

        assert data.verbose_name == 'person'
        assert data.verbose_name_plural == 'people'


def generator(max_value):
    for i in range(max_value):
        yield {
            'foo': i,
            'bar': chr(i),
            'baz': hex(i),
            'inv': max_value - i
        }


class TableListsDataTest(TestCase):
    def test_TableListData_basic_list(self):
        list_data = list(generator(100))
        data = TableListData(list_data)

        assert len(list_data) == len(data)
        assert data.verbose_name == 'item'
        assert data.verbose_name_plural == 'items'

    def test_TableListData_with_verbose_name(self):
        '''
        TableListData uses the attributes on the listlike object to generate
        it's verbose_name.
        '''
        class listlike(list):
            verbose_name = 'unit'
            verbose_name_plural = 'units'

        list_data = listlike(generator(100))
        data = TableListData(list_data)

        assert len(list_data) == len(data)
        assert data.verbose_name == 'unit'
        assert data.verbose_name_plural == 'units'


class CustomTableQuerysetData(TestCase):
    def test_custom_TableData(self):
        '''If TableQuerysetData._length is set, no count() query will be performed'''
        for i in range(20):
            Person.objects.create(first_name='first {}'.format(i))

        data = TableQuerysetData(Person.objects.all())
        data._length = 10

        table = Table(data=data)
        self.assertEqual(len(table.data), 10)
