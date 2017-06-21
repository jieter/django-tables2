# coding: utf-8
'''Test the core table functionality.'''
from __future__ import absolute_import, unicode_literals

import copy
import itertools

import pytest
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator

import django_tables2 as tables
from django_tables2.tables import DeclarativeColumnsMetaclass

from .utils import build_request, parse, attrs

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


def test_column_named_items():
    '''
    A column named items must not make the table fail
    https://github.com/bradleyayers/django-tables2/issues/316
    '''
    class ItemsTable(tables.Table):
        items = tables.Column()

    table = ItemsTable([{'items': 123}, {'items': 2345}])

    html = table.as_html(request)
    assert '123' in html
    assert '2345' in html


def test_declarations():
    '''Test defining tables by declaration.'''
    class GeoAreaTable(tables.Table):
        name = tables.Column()
        population = tables.Column()

    assert len(GeoAreaTable.base_columns) == 2
    assert 'name' in GeoAreaTable.base_columns
    assert not hasattr(GeoAreaTable, 'name')

    class CountryTable(GeoAreaTable):
        capital = tables.Column()

    assert len(CountryTable.base_columns) == 3
    assert 'capital' in CountryTable.base_columns

    # multiple inheritance
    class AddedMixin(tables.Table):
        added = tables.Column()

    class CityTable(GeoAreaTable, AddedMixin):
        mayor = tables.Column()

    assert len(CityTable.base_columns) == 4
    assert 'added' in CityTable.base_columns

    # overwrite a column with a non-column
    class MayorlessCityTable(CityTable):
        mayor = None

    assert len(MayorlessCityTable.base_columns) == 3


def test_metaclass_inheritance():
    class Tweaker(type):
        '''Adds an attribute "tweaked" to all classes'''
        def __new__(cls, name, bases, attrs):
            attrs['tweaked'] = True
            return super(Tweaker, cls).__new__(cls, name, bases, attrs)

    class Meta(Tweaker, DeclarativeColumnsMetaclass):
        pass

    class TweakedTableBase(tables.Table):
        __metaclass__ = Meta
        name = tables.Column()

    # Python 2/3 compatible way to enable the metaclass
    TweakedTable = Meta(str('TweakedTable'), (TweakedTableBase, ), {})

    table = TweakedTable([])
    assert 'name' in table.columns
    assert table.tweaked

    # now flip the order
    class FlippedMeta(DeclarativeColumnsMetaclass, Tweaker):
        pass

    class FlippedTweakedTableBase(tables.Table):
        name = tables.Column()

    # Python 2/3 compatible way to enable the metaclass
    FlippedTweakedTable = FlippedMeta(str('FlippedTweakedTable'), (FlippedTweakedTableBase, ), {})

    table = FlippedTweakedTable([])
    assert 'name' in table.columns
    assert table.tweaked


def test_attrs():
    class TestTable(tables.Table):
        class Meta:
            attrs = {}
    assert {} == TestTable([]).attrs

    class TestTable2(tables.Table):
        class Meta:
            attrs = {'a': 'b'}
    assert {'a': 'b'} == TestTable2([]).attrs

    class TestTable3(tables.Table):
        pass
    assert {} == TestTable3([]).attrs
    assert {'a': 'b'} == TestTable3([], attrs={'a': 'b'}).attrs

    class TestTable4(tables.Table):
        class Meta:
            attrs = {'a': 'b'}
    assert {'c': 'd'} == TestTable4([], attrs={'c': 'd'}).attrs


def test_attrs_support_computed_values():
    counter = itertools.count()

    class TestTable(tables.Table):
        class Meta:
            attrs = {'id': lambda: 'test_table_%d' % next(counter)}

    assert 'id="test_table_0"' == TestTable([]).attrs.as_html()
    assert 'id="test_table_1"' == TestTable([]).attrs.as_html()


def test_attrs_from_settings(settings):
    settings.DJANGO_TABLES2_TABLE_ATTRS = {
        'class': 'table-compact'
    }

    class Table(tables.Table):
        column = tables.Column()

    table = Table({})
    assert table.attrs == {'class': 'table-compact'}


def test_datasource_untouched():
    '''
    Ensure that data that is provided to the table (the datasource) is not
    modified by table operations.
    '''
    original_data = copy.deepcopy(MEMORY_DATA)

    table = UnorderedTable(MEMORY_DATA)
    table.order_by = 'i'
    list(table.rows)
    assert MEMORY_DATA == original_data

    table = UnorderedTable(MEMORY_DATA)
    table.order_by = 'beta'
    list(table.rows)
    assert MEMORY_DATA == original_data


def test_should_support_tuple_data_source():
    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable((
        {'name': 'brad'},
        {'name': 'davina'},
    ))

    assert len(table.rows) == 2


# @pytest.mark.django_db
# def test_should_support_haystack_data_source():
#     Person.objects.create(first_name='Foo', last_name='Bar')
#     Person.objects.create(first_name='Brad', last_name='Pitt')
#
#     from haystack.query import SearchQuerySet
#     from haystack.management.commands import update_index
#
#     update_index.Command().handle(interactive=False)
#
#     class PersonTable(tables.Table):
#         first_name = tables.Column()
#
#     table = PersonTable(SearchQuerySet().all())
#     html = table.as_html(request)
#
#     # TODO: assert that a person is actually in the produced html.
#     assert 'Brad' in html
#

def test_column_count():
    class SimpleTable(tables.Table):
        visible = tables.Column(visible=True)
        hidden = tables.Column(visible=False)

    # The columns container supports the len() builtin
    assert len(SimpleTable([]).columns) == 1


def test_column_accessor():
    class SimpleTable(UnorderedTable):
        col1 = tables.Column(accessor='alpha.upper.isupper')
        col2 = tables.Column(accessor='alpha.upper')
    table = SimpleTable(MEMORY_DATA)

    assert table.rows[0].get_cell('col1') is True
    assert table.rows[0].get_cell('col2') == 'B'


def test_exclude_columns():
    '''
    Defining ``Table.Meta.exclude`` or providing an ``exclude`` argument when
    instantiating a table should have the same effect -- exclude those columns
    from the table. It should have the same effect as not defining the
    columns originally.
    '''
    table = UnorderedTable([], exclude=('i'))
    assert table.columns.names() == ['alpha', 'beta']

    # Table.Meta: exclude=...
    class PartialTable(UnorderedTable):
        class Meta:
            exclude = ('alpha', )
    table = PartialTable([])
    assert table.columns.names() == ['i', 'beta']

    # Inheritence -- exclude in parent, add in child
    class AddonTable(PartialTable):
        added = tables.Column()
    table = AddonTable([])
    assert table.columns.names() == ['i', 'beta', 'added']

    # Inheritence -- exclude in child
    class ExcludeTable(UnorderedTable):
        added = tables.Column()

        class Meta:
            exclude = ('beta', )

    table = ExcludeTable([])
    assert table.columns.names() == ['i', 'alpha', 'added']


def test_table_exclude_property_should_override_constructor_argument():
    class SimpleTable(tables.Table):
        a = tables.Column()
        b = tables.Column()

    table = SimpleTable([], exclude=('b', ))
    assert table.columns.names() == ['a']
    table.exclude = ('a', )
    assert table.columns.names() == ['b']


def test_exclude_should_work_on_sequence_too():
    '''
    It should be possible to define a sequence on a table
    and exclude it in a child of that table.
    '''
    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()
        occupation = tables.Column()

        class Meta:
            sequence = ('first_name', 'last_name', 'occupation')

    class AnotherPersonTable(PersonTable):
        class Meta(PersonTable.Meta):
            exclude = ('first_name', 'last_name')

    tableA = PersonTable([])
    assert tableA.columns.names() == ['first_name', 'last_name', 'occupation']

    tableB = AnotherPersonTable([])
    assert tableB.columns.names() == ['occupation']

    tableC = PersonTable([], exclude=('first_name'))
    assert tableC.columns.names() == ['last_name', 'occupation']


def test_pagination():
    class BookTable(tables.Table):
        name = tables.Column()

    # create some sample data
    data = []
    for i in range(100):
        data.append({'name': 'Book No. %d' % i})
    books = BookTable(data)

    # external paginator
    paginator = Paginator(books.rows, 10)
    assert paginator.num_pages == 10
    page = paginator.page(1)
    assert page.has_previous() is False
    assert page.has_next() is True

    # integrated paginator
    books.paginate(page=1)
    assert hasattr(books, 'page') is True

    books.paginate(page=1, per_page=10)
    assert len(list(books.page.object_list)) == 10

    # new attributes
    assert books.paginator.num_pages == 10
    assert books.page.has_previous() is False
    assert books.page.has_next() is True

    # accessing a non-existant page raises 404
    with pytest.raises(EmptyPage):
        books.paginate(Paginator, page=9999, per_page=10)

    with pytest.raises(PageNotAnInteger):
        books.paginate(Paginator, page='abc', per_page=10)


def test_pagination_shouldnt_prevent_multiple_rendering():
    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable([{'name': 'brad'}])
    table.paginate()

    assert table.as_html(request) == table.as_html(request)


def test_empty_text():
    class TestTable(tables.Table):
        a = tables.Column()

    table = TestTable([])
    assert table.empty_text is None

    class TestTable2(tables.Table):
        a = tables.Column()

        class Meta:
            empty_text = 'nothing here'

    table = TestTable2([])
    assert table.empty_text == 'nothing here'

    table = TestTable2([], empty_text='still nothing')
    assert table.empty_text == 'still nothing'


def test_prefix():
    '''
    Test that table prefixes affect the names of querystring parameters
    '''
    class TableA(tables.Table):
        name = tables.Column()

        class Meta:
            prefix = 'x'

    table = TableA([])
    html = table.as_html(build_request('/'))

    assert 'x' == table.prefix
    assert 'xsort=name' in html

    class TableB(tables.Table):
        last_name = tables.Column()

    assert '' == TableB([]).prefix
    assert 'x' == TableB([], prefix='x').prefix

    table = TableB([])
    table.prefix = 'x-'
    html = table.as_html(build_request('/'))

    assert 'x-' == table.prefix
    assert 'x-sort=last_name' in html


def test_field_names():
    class TableA(tables.Table):
        class Meta:
            order_by_field = 'abc'
            page_field = 'def'
            per_page_field = 'ghi'

    table = TableA([])
    assert 'abc' == table.order_by_field
    assert 'def' == table.page_field
    assert 'ghi' == table.per_page_field


def test_field_names_with_prefix():
    class TableA(tables.Table):
        class Meta:
            order_by_field = 'sort'
            page_field = 'page'
            per_page_field = 'per_page'
            prefix = '1-'

    table = TableA([])
    assert '1-sort' == table.prefixed_order_by_field
    assert '1-page' == table.prefixed_page_field
    assert '1-per_page' == table.prefixed_per_page_field

    class TableB(tables.Table):
        class Meta:
            order_by_field = 'sort'
            page_field = 'page'
            per_page_field = 'per_page'

    table = TableB([], prefix='1-')
    assert '1-sort' == table.prefixed_order_by_field
    assert '1-page' == table.prefixed_page_field
    assert '1-per_page' == table.prefixed_per_page_field

    table = TableB([])
    table.prefix = '1-'
    assert '1-sort' == table.prefixed_order_by_field
    assert '1-page' == table.prefixed_page_field
    assert '1-per_page' == table.prefixed_per_page_field


def test_should_support_a_template_to_be_specified():
    class ConstructorSpecifiedTemplateTable(tables.Table):
        name = tables.Column()

    table = ConstructorSpecifiedTemplateTable([], template='dummy.html')
    assert table.template == 'dummy.html'

    class PropertySpecifiedTemplateTable(tables.Table):
        name = tables.Column()

    table = PropertySpecifiedTemplateTable([])
    table.template = 'dummy.html'
    assert table.template == 'dummy.html'

    class DefaultTable(tables.Table):
        pass

    table = DefaultTable([])
    assert table.template == 'django_tables2/table.html'


def test_template_in_meta_class_declaration_should_be_honored():
    class MetaDeclarationSpecifiedTemplateTable(tables.Table):
        name = tables.Column()

        class Meta:
            template = 'dummy.html'

    table = MetaDeclarationSpecifiedTemplateTable([])
    assert table.template == 'dummy.html'
    assert table.as_html(request) == 'dummy template contents\n'


def test_should_support_rendering_multiple_times():
    class MultiRenderTable(tables.Table):
        name = tables.Column()

    # test list data
    table = MultiRenderTable([{'name': 'brad'}])
    assert table.as_html(request) == table.as_html(request)


def test_column_defaults_are_honored():
    class Table(tables.Table):
        name = tables.Column(default='abcd')

        class Meta:
            default = 'efgh'

    table = Table([{}], default='ijkl')
    assert table.rows[0].get_cell('name') == 'abcd'


def test_table_meta_defaults_are_honored():
    class Table(tables.Table):
        name = tables.Column()

        class Meta:
            default = 'abcd'

    table = Table([{}])
    assert table.rows[0].get_cell('name') == 'abcd'


def test_table_defaults_are_honored():
    class Table(tables.Table):
        name = tables.Column()

    table = Table([{}], default='abcd')
    assert table.rows[0].get_cell('name') == 'abcd'

    table = Table([{}], default='abcd')
    table.default = 'efgh'
    assert table.rows[0].get_cell('name') == 'efgh'


def test_as_values():
    class Table(tables.Table):
        name = tables.Column()
        country = tables.Column()

    data = [
        {'name': 'Adrian', 'country': 'Australia'},
        {'name': 'Adrian', 'country': 'Brazil'},
        {'name': 'Audrey', 'country': 'Chile'},
        {'name': 'Bassie', 'country': 'Belgium'},
    ]
    expected = [['Name', 'Country']] + [[r['name'], r['country']] for r in data]
    table = Table(data)

    assert list(table.as_values()) == expected


def test_as_values_empty_values():
    '''
    Table's as_values() method returns `None` for missing values
    '''

    class Table(tables.Table):
        name = tables.Column()
        country = tables.Column()

    data = [
        {'name': 'Adrian', 'country': 'Brazil'},
        {'name': 'Audrey'},
        {'name': 'Bassie', 'country': 'Belgium'},
        {'country': 'France'},
    ]
    expected = [['Name', 'Country']] + [[r.get('name'), r.get('country')] for r in data]
    table = Table(data)
    assert list(table.as_values()) == expected


def test_row_attrs():
    class Table(tables.Table):
        alpha = tables.Column()
        beta = tables.Column()

    table = Table(MEMORY_DATA, row_attrs={
        'class': lambda record: 'row-id-{}'.format(record['i']),
    })

    assert table.rows[0].attrs == {'class': 'row-id-2 even'}


def test_row_attrs_in_meta():
    class Table(tables.Table):
        alpha = tables.Column()
        beta = tables.Column()

        class Meta:
            row_attrs = {
                'class': lambda record: 'row-id-{}'.format(record['i']),
            }

    table = Table(MEMORY_DATA)
    assert table.rows[0].attrs == {'class': 'row-id-2 even'}


def test_td_attrs_from_table():
    class Table(tables.Table):
        alpha = tables.Column()
        beta = tables.Column()

        class Meta:
            attrs = {
                'td': {
                    'data-column-name': lambda column: column.name
                }
            }
    table = Table(MEMORY_DATA)
    html = table.as_html(request)
    td = parse(html).find('.//tbody/tr[1]/td[1]')
    assert td.attrib == {
        'data-column-name': 'alpha',
        'class': 'alpha'
    }
