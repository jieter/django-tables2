# coding: utf-8
from __future__ import absolute_import, unicode_literals

import django_tables2 as tables
from django.utils import six
from django_tables2.tables import RequestConfig

import pytest

from .app.models import Person
from .utils import build_request

request = build_request('/')


MEMORY_DATA = [
    {'i': 2, 'alpha': 'b', 'beta': 'b'},
    {'i': 1, 'alpha': 'a', 'beta': 'c'},
    {'i': 3, 'alpha': 'c', 'beta': 'a'},
]


class UnorderedTable(tables.Table):
    i = tables.Column()
    alpha = tables.Column()
    beta = tables.Column()


class OrderedTable(UnorderedTable):
    class Meta:
        order_by = 'alpha'


def test_ordering():
    # fallback to Table.Meta
    assert ('alpha', ) == OrderedTable([], order_by=None).order_by == OrderedTable([]).order_by

    # values of order_by are wrapped in tuples before being returned
    assert OrderedTable([], order_by='alpha').order_by == ('alpha', )
    assert OrderedTable([], order_by=('beta', )).order_by == ('beta', )

    table = OrderedTable([])
    table.order_by = []
    assert () == table.order_by == OrderedTable([], order_by=[]).order_by

    table = OrderedTable([])
    table.order_by = ()
    assert () == table.order_by == OrderedTable([], order_by=()).order_by

    table = OrderedTable([])
    table.order_by = ''
    assert () == table.order_by == OrderedTable([], order_by='').order_by

    # apply an ordering
    table = UnorderedTable([])
    table.order_by = 'alpha'
    assert ('alpha', ) == UnorderedTable([], order_by='alpha').order_by == table.order_by

    table = OrderedTable([])
    table.order_by = 'alpha'
    assert ('alpha', ) == OrderedTable([], order_by='alpha').order_by == table.order_by

    # let's check the data
    table = OrderedTable(MEMORY_DATA, order_by='beta')
    assert 3 == table.rows[0].get_cell('i')

    table = OrderedTable(MEMORY_DATA, order_by='-beta')
    assert 1 == table.rows[0].get_cell('i')

    # allow fallback to Table.Meta.order_by
    table = OrderedTable(MEMORY_DATA)
    assert 1 == table.rows[0].get_cell('i')

    # column's can't be ordered if they're not allowed to be
    class TestTable2(tables.Table):
        a = tables.Column(orderable=False)
        b = tables.Column()

    table = TestTable2([], order_by='a')
    assert table.order_by == ()

    table = TestTable2([], order_by='b')
    assert table.order_by == ('b', )

    # ordering disabled by default
    class TestTable3(tables.Table):
        a = tables.Column(orderable=True)
        b = tables.Column()

        class Meta:
            orderable = False

    table = TestTable3([], order_by='a')
    assert table.order_by == ('a', )

    table = TestTable3([], order_by='b')
    assert table.order_by == ()

    table = TestTable3([], orderable=True, order_by='b')
    assert table.order_by == ('b', )


def test_ordering_different_types():
    from datetime import datetime

    data = [
        {'i': 1, 'alpha': datetime.now(), 'beta': [1]},
        {'i': {}, 'alpha': None, 'beta': ''},
        {'i': 2, 'alpha': None, 'beta': []},
    ]

    table = OrderedTable(data)
    assert '—' == table.rows[0].get_cell('alpha')

    table = OrderedTable(data, order_by='i')
    if six.PY3:
        assert {} == table.rows[0].get_cell('i')
    else:
        assert 1 == table.rows[0].get_cell('i')

    table = OrderedTable(data, order_by='beta')
    assert [] == table.rows[0].get_cell('beta')


brad = {'first_name': 'Bradley', 'last_name': 'Ayers'}
brad2 = {'first_name': 'Bradley', 'last_name': 'Fake'}
chris = {'first_name': 'Chris', 'last_name': 'Doble'}
davina = {'first_name': 'Davina', 'last_name': 'Adisusila'}
ross = {'first_name': 'Ross', 'last_name': 'Ayers'}

people = [brad, brad2, chris, davina, ross]


def test_multi_column_ordering_by_table():

    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()

    table = PersonTable(people, order_by=('first_name', 'last_name'))
    assert [brad, brad2, chris, davina, ross] == [r.record for r in table.rows]

    table = PersonTable(people, order_by=('first_name', '-last_name'))
    assert [brad2, brad, chris, davina, ross] == [r.record for r in table.rows]


def test_multi_column_ordering_by_column():
    # let's try column order_by using multiple keys
    class PersonTable(tables.Table):
        name = tables.Column(order_by=('first_name', 'last_name'))

    # add 'name' key for each person.
    for person in people:
        person['name'] = '{p[first_name]} {p[last_name]}'.format(p=person)
    assert brad['name'] == 'Bradley Ayers'

    table = PersonTable(people, order_by='name')
    assert [brad, brad2, chris, davina, ross] == [r.record for r in table.rows]

    table = PersonTable(people, order_by='-name')
    assert [ross, davina, chris, brad2, brad] == [r.record for r in table.rows]


@pytest.mark.django_db
def test_ordering_by_custom_field():
    '''
    When defining a custom field in a table, as name=tables.Column() with
    methods to render and order render_name and order_name, sorting by this
    column causes an error if the custom field is not in last position.
    (issue #413)
    '''

    Person.objects.create(first_name='Alice', last_name='Beta')
    Person.objects.create(first_name='Bob', last_name='Alpha')

    from django.db.models import F, Value
    from django.db.models.functions import Concat

    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()
        full_name = tables.Column()

        def render_full_name(self, record):
            return record.last_name + ' ' + record.first_name

        def order_full_name(self, queryset, is_descending):
            queryset = queryset.annotate(
                full_name=Concat(F('last_name'), Value(' '), F('first_name'))
            ).order_by(('-' if is_descending else '') + 'full_name')
            return queryset, True

        class Meta:
            model = Person
            fields = ('first_name', 'last_name', 'full_name')

    table = PersonTable(Person.objects.all())
    request = build_request('/?sort=full_name&sort=first_name')
    RequestConfig(request).configure(table)

    assert table.rows[0].record.first_name == 'Bob'


def test_list_table_data_supports_ordering():
    class Table(tables.Table):
        name = tables.Column()

    data = [
        {'name': 'Bradley'},
        {'name': 'Davina'},
    ]

    table = Table(data)
    assert table.rows[0].get_cell('name') == 'Bradley'
    table.order_by = '-name'
    assert table.rows[0].get_cell('name') == 'Davina'


def test_ordering_non_database_data():
    class Table(tables.Table):
        name = tables.Column()
        country = tables.Column()

    data = [
        {'name': 'Adrian', 'country': 'Australia'},
        {'name': 'Adrian', 'country': 'Brazil'},
        {'name': 'Audrey', 'country': 'Chile'},
        {'name': 'Bassie', 'country': 'Belgium'},
    ]
    table = Table(data, order_by=('-name', '-country'))

    assert table.rows[0].get_cell('name') == 'Bassie'
    assert table.rows[1].get_cell('name') == 'Audrey'
    assert table.rows[2].get_cell('name') == 'Adrian'
    assert table.rows[2].get_cell('country') == 'Brazil'
    assert table.rows[3].get_cell('name') == 'Adrian'
    assert table.rows[3].get_cell('country') == 'Australia'


def test_table_ordering_attributes():
    class Table(tables.Table):
        alpha = tables.Column()
        beta = tables.Column()

    table = Table(MEMORY_DATA, attrs={
        'th': {
            'class': 'custom-header-class',
            '_ordering': {
                'orderable': 'sortable',
                'ascending': 'ascend',
                'descending': 'descend',
            },
        },
    }, order_by='alpha')

    assert 'sortable' in table.columns[0].attrs['th']['class']
    assert 'ascend' in table.columns[0].attrs['th']['class']
    assert 'custom-header-class' in table.columns[1].attrs['th']['class']


def test_table_ordering_attributes_in_meta():
    class Table(tables.Table):
        alpha = tables.Column()
        beta = tables.Column()

        class Meta(OrderedTable.Meta):
            attrs = {
                'th': {
                    'class': 'custom-header-class-in-meta',
                    '_ordering': {
                        'orderable': 'sortable',
                        'ascending': 'ascend',
                        'descending': 'descend',
                    },
                }
            }

    table = Table(MEMORY_DATA)

    assert 'sortable' in table.columns[0].attrs['th']['class']
    assert 'ascend' in table.columns[0].attrs['th']['class']
    assert 'custom-header-class-in-meta' in table.columns[1].attrs['th']['class']


def test_column_ordering_attributes():
    class Table(tables.Table):
        alpha = tables.Column(attrs={
            'th': {
                'class': 'custom-header-class',
                '_ordering': {
                    'orderable': 'sort',
                    'ascending': 'ascending'
                }
            }
        })
        beta = tables.Column(attrs={
            'th': {
                '_ordering': {
                    'orderable': 'canOrder',
                }
            },
            'td': {
                'class': 'cell-2'
            }
        })

    table = Table(MEMORY_DATA, attrs={'class': 'only-on-table'}, order_by='alpha')

    assert 'only-on-table' not in table.columns[0].attrs['th']['class']
    assert 'custom-header-class' in table.columns[0].attrs['th']['class']
    assert 'ascending' in table.columns[0].attrs['th']['class']
    assert 'sort' in table.columns[0].attrs['th']['class']
    assert 'canOrder' in table.columns[1].attrs['th']['class']
