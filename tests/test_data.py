
from django_tables2.tables import TableListData


def generator(max_value):
    for i in range(max_value):
        yield {
            'foo': i,
            'bar': chr(i),
            'baz': hex(i),
            'inv': max_value - i
        }


def test_TableListData_basic_list():
    l = list(generator(100))
    data = TableListData(l, object())

    assert len(l) == len(data)
    assert data.verbose_name == 'item'
    assert data.verbose_name_plural == 'items'


def test_TableListData_with_verbose_name():
    '''
    TableListData uses the attributes on the listlike object to generate
    it's verbose_name.
    '''
    class listlike(list):
        verbose_name = 'unit'
        verbose_name_plural = 'units'

    l = listlike(generator(100))
    data = TableListData(l, object())

    assert len(data) == len(l)
    assert data.verbose_name == 'unit'
    assert data.verbose_name_plural == 'units'
