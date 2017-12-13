# coding: utf-8
from __future__ import unicode_literals

from django.test import TestCase

from django_tables2.data import TableData, TableListData, TableQuerysetData

from .app.models import Person


class TableDataFactoryTest(TestCase):
    def test_invalid_data_None(self):
        with self.assertRaises(ValueError):
            TableData.from_data(None, table={})

    def test_invalid_data_int(self):
        with self.assertRaises(ValueError):
            TableData.from_data(1, table={})

    def test_invalid_data_classes(self):
        class Klass(object):
            pass

        with self.assertRaises(ValueError):
            TableData.from_data(Klass(), table={})

        class Bad(object):
            def __len__(self):
                pass

        with self.assertRaises(ValueError):
            TableData.from_data(Bad(), table={})

    def test_valid_QuerySet(self):
        data = TableData.from_data(Person.objects.all(), table={})
        assert isinstance(data, TableQuerysetData)

    def test_valid_list_of_dicts(self):
        data = TableData.from_data([{'name': 'John'}, {'name': 'Pete'}], table={})
        assert isinstance(data, TableListData)
        assert len(data) == 2

    def test_valid_tuple_of_dicts(self):
        data = TableData.from_data(({'name': 'John'}, {'name': 'Pete'}), table={})
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

        data = TableData.from_data(Datasource(), table={})
        assert len(data) == 1


class TableDataTest(TestCase):
    def test_knows_its_default_name(self):
        data = TableData.from_data([{}], table={})
        assert data.verbose_name == 'item'
        assert data.verbose_name_plural == 'items'

    def test_knows_its_name(self):
        data = TableData.from_data(Person.objects.all(), table={})

        assert data.verbose_name == 'person'
        assert data.verbose_name_plural == 'people'
