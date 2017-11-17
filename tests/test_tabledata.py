# coding: utf-8
from __future__ import unicode_literals

import pytest

from django_tables2.data import TableData, TableListData, TableQuerysetData

from .app.models import Person


def test_TableData_factory_invalid_data_None():
    with pytest.raises(ValueError):
        TableData.from_data(None, table={})


def test_TableData_factory_invalid_data_int():
    with pytest.raises(ValueError):
        TableData.from_data(1, table={})


def test_TableData_factory_invalid_data_classes():
    class Klass(object):
        pass

    with pytest.raises(ValueError):
        TableData.from_data(Klass(), table={})

    class Bad(object):
        def __len__(self):
            pass

    with pytest.raises(ValueError):
        TableData.from_data(Bad(), table={})


@pytest.mark.django_db
def test_TableData_factory_valid_QuerySet():
    data = TableData.from_data(Person.objects.all(), table={})
    assert isinstance(data, TableQuerysetData)


def test_TableData_factory_valid_list_of_dicts():
    data = TableData.from_data([{'name': 'John'}, {'name': 'Pete'}], table={})
    assert isinstance(data, TableListData)
    assert len(data) == 2


def test_TableData_factory_valid_tuple_of_dicts():
    data = TableData.from_data(({'name': 'John'}, {'name': 'Pete'}), table={})
    assert isinstance(data, TableListData)
    assert len(data) == 2


def test_TableData_factory_valid_class():
    class Datasource(object):
        def __len__(self):
            return 1

        def __getitem__(self, pos):
            if pos != 0:
                raise IndexError()
            return {'a': 1}

    data = TableData.from_data(Datasource(), table={})
    assert len(data) == 1


def test_tabledata_knows_its_default_name():
    data = TableData.from_data([{}], table={})
    assert data.verbose_name == 'item'
    assert data.verbose_name_plural == 'items'


def test_tabledata_knows_its_name():
    data = TableData.from_data(Person.objects.all(), table={})

    assert data.verbose_name == 'person'
    assert data.verbose_name_plural == 'people'
