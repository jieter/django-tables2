
from django.test import TestCase

from django_tables2.data import TableListData


def generator(max_value):
    for i in range(max_value):
        yield {
            'foo': i,
            'bar': chr(i),
            'baz': hex(i),
            'inv': max_value - i
        }


class DataTest(TestCase):
    def test_TableListData_basic_list(self):
        list_data = list(generator(100))
        data = TableListData(list_data, object())

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
        data = TableListData(list_data, object())

        assert len(list_data) == len(data)
        assert data.verbose_name == 'unit'
        assert data.verbose_name_plural == 'units'
