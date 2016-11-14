# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.db import models
from django.utils.safestring import SafeData, mark_safe
from django.utils.translation import ugettext_lazy

import django_tables2 as tables

from ..app.models import Person
from ..utils import build_request, parse

request = build_request('/')


def test_column_render_supports_kwargs():
    class TestColumn(tables.Column):
        def render(self, **kwargs):
            expected = {'record', 'value', 'column', 'bound_column', 'bound_row', 'table'}
            actual = set(kwargs.keys())
            assert actual == expected
            return 'success'

    class TestTable(tables.Table):
        foo = TestColumn()

    table = TestTable([{'foo': 'bar'}])
    assert table.rows[0].get_cell('foo') == 'success'


def test_column_header_should_use_titlised_verbose_name_unless_given_explicitly():
    class SimpleTable(tables.Table):
        basic = tables.Column()
        acronym = tables.Column(verbose_name='has FBI help')

    table = SimpleTable([])
    assert table.columns['basic'].header == 'Basic'
    assert table.columns['acronym'].header == 'has FBI help'


def test_should_support_safe_verbose_name():
    class SimpleTable(tables.Table):
        safe = tables.Column(verbose_name=mark_safe('<b>Safe</b>'))

    table = SimpleTable([])
    assert isinstance(table.columns['safe'].header, SafeData)


def test_should_raise_on_invalid_accessor():
    with pytest.raises(TypeError):
        class SimpleTable(tables.Table):
            column = tables.Column(accessor={})


def test_column_with_callable_accessor_should_not_have_default():
    with pytest.raises(TypeError):
        class SimpleTable(tables.Table):
            column = tables.Column(accessor=lambda: 'foo', default='')


def test_should_support_safe_verbose_name_via_model():
    class PersonTable(tables.Table):
        safe = tables.Column()

    table = PersonTable(Person.objects.all())
    assert isinstance(table.columns['safe'].header, SafeData)


def test_should_support_empty_string_as_explicit_verbose_name():
    class SimpleTable(tables.Table):
        acronym = tables.Column(verbose_name='')

    table = SimpleTable([])
    assert table.columns['acronym'].header == ''


@pytest.mark.django_db
def test_handle_verbose_name_of_many2onerel():

    class Table(tables.Table):
        count = tables.Column(accessor='info_list.count')

    Person.objects.create(first_name='bradley', last_name='ayers')
    table = Table(Person.objects.all())
    assert table.columns['count'].verbose_name == 'Information'


def test_orderable():
    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable([])
    assert table.columns['name'].orderable is True

    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            orderable = False
    table = SimpleTable([])
    assert table.columns['name'].orderable is False

    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            orderable = True

    table = SimpleTable([])
    assert table.columns['name'].orderable is True


def test_order_by_defaults_to_accessor():
    class SimpleTable(tables.Table):
        foo = tables.Column(accessor='bar')

    table = SimpleTable([])
    assert table.columns['foo'].order_by == ('bar', )


def test_supports_order_by():
    class SimpleTable(tables.Table):
        name = tables.Column(order_by=('last_name', '-first_name'))
        age = tables.Column()

    table = SimpleTable([], order_by=('-age', ))
    # alias
    assert table.columns['name'].order_by_alias == 'name'
    assert table.columns['age'].order_by_alias == '-age'
    # order by
    assert table.columns['name'].order_by == ('last_name', '-first_name')
    assert table.columns['age'].order_by == ('-age', )

    # now try with name ordered
    table = SimpleTable([], order_by=('-name', ))
    # alias
    assert table.columns['name'].order_by_alias == '-name'
    assert table.columns['age'].order_by_alias == 'age'
    # alias next
    assert table.columns['name'].order_by_alias.next == 'name'
    assert table.columns['age'].order_by_alias.next == 'age'
    # order by
    assert table.columns['name'].order_by == ('-last_name', 'first_name')
    assert table.columns['age'].order_by == ('age', )


def test_supports_is_ordered():
    class SimpleTable(tables.Table):
        name = tables.Column()

    # sorted
    table = SimpleTable([], order_by='name')
    assert table.columns['name'].is_ordered
    # unsorted
    table = SimpleTable([])
    assert not table.columns['name'].is_ordered


def test_translation():
    '''
    Tests different types of values for the ``verbose_name`` property of a
    column.
    '''
    class TranslationTable(tables.Table):
        text = tables.Column(verbose_name=ugettext_lazy('Text'))

    table = TranslationTable([])
    assert 'Text' == table.columns['text'].header


def test_sequence():
    '''
    Ensures that the sequence of columns is configurable.
    '''
    class TestTable(tables.Table):
        a = tables.Column()
        b = tables.Column()
        c = tables.Column()
    assert ['a', 'b', 'c'] == TestTable([]).columns.names()
    assert ['b', 'a', 'c'] == TestTable([], sequence=('b', 'a', 'c')).columns.names()

    class TestTable2(TestTable):
        class Meta:
            sequence = ('b', 'a', 'c')
    assert ['b', 'a', 'c'] == TestTable2([]).columns.names()
    assert ['a', 'b', 'c'] == TestTable2([], sequence=('a', 'b', 'c')).columns.names()

    class TestTable3(TestTable):
        class Meta:
            sequence = ('c', )
    assert ['c', 'a', 'b'] == TestTable3([]).columns.names()
    assert ['c', 'a', 'b'] == TestTable([], sequence=('c', )).columns.names()

    class TestTable4(TestTable):
        class Meta:
            sequence = ('...', )
    assert ['a', 'b', 'c'] == TestTable4([]).columns.names()
    assert ['a', 'b', 'c'] == TestTable([], sequence=('...', )).columns.names()

    class TestTable5(TestTable):
        class Meta:
            sequence = ('b', '...')
    assert ['b', 'a', 'c'] == TestTable5([]).columns.names()
    assert ['b', 'a', 'c'] == TestTable([], sequence=('b', '...')).columns.names()

    class TestTable6(TestTable):
        class Meta:
            sequence = ('...', 'b')
    assert ['a', 'c', 'b'] == TestTable6([]).columns.names()
    assert ['a', 'c', 'b'] == TestTable([], sequence=('...', 'b')).columns.names()

    class TestTable7(TestTable):
        class Meta:
            sequence = ('b', '...', 'a')
    assert ['b', 'c', 'a'] == TestTable7([]).columns.names()
    assert ['b', 'c', 'a'] == TestTable([], sequence=('b', '...', 'a')).columns.names()

    # Let's test inheritence
    class TestTable8(TestTable):
        d = tables.Column()
        e = tables.Column()
        f = tables.Column()

        class Meta:
            sequence = ('d', '...')

    class TestTable9(TestTable):
        d = tables.Column()
        e = tables.Column()
        f = tables.Column()

    assert ['d', 'a', 'b', 'c', 'e', 'f'] == TestTable8([]).columns.names()
    assert ['d', 'a', 'b', 'c', 'e', 'f'] == TestTable9([], sequence=('d', '...')).columns.names()


def test_should_support_both_meta_sequence_and_constructor_exclude():
    '''
    Issue #32 describes a problem when both ``Meta.sequence`` and
    ``Table(..., exclude=...)`` are used on a single table. The bug caused an
    exception to be raised when the table was iterated.
    '''
    class SequencedTable(tables.Table):
        a = tables.Column()
        b = tables.Column()
        c = tables.Column()

        class Meta:
            sequence = ('a', '...')

    table = SequencedTable([], exclude=('c', ))
    table.as_html(request)


def test_bound_columns_should_support_indexing():
    class SimpleTable(tables.Table):
        a = tables.Column()
        b = tables.Column()

    table = SimpleTable([])
    assert 'b' == table.columns[1].name
    assert 'b' == table.columns['b'].name


def test_cell_attrs_applies_to_td_and_th():
    class SimpleTable(tables.Table):
        a = tables.Column(attrs={'cell': {'key': 'value'}})

    # providing data ensures 1 row is rendered
    table = SimpleTable([{'a': 'value'}])
    root = parse(table.as_html(request))

    assert root.findall('.//thead/tr/th')[0].attrib == {'key': 'value', 'class': 'a orderable'}
    assert root.findall('.//tbody/tr/td')[0].attrib == {'key': 'value', 'class': 'a'}


def test_cells_are_automatically_given_column_name_as_class():
    class SimpleTable(tables.Table):
        a = tables.Column()

    table = SimpleTable([{'a': 'value'}])
    root = parse(table.as_html(request))
    assert root.findall('.//thead/tr/th')[0].attrib == {'class': 'a orderable'}
    assert root.findall('.//tbody/tr/td')[0].attrib == {'class': 'a'}


def test_th_are_given_orderable_class_if_column_is_orderable():
    class SimpleTable(tables.Table):
        a = tables.Column()
        b = tables.Column(orderable=False)

    table = SimpleTable([{'a': 'value'}])
    root = parse(table.as_html(request))
    # return classes of an element as a set
    classes = lambda x: set(x.attrib['class'].split())
    assert 'orderable' in classes(root.findall('.//thead/tr/th')[0])
    assert 'orderable' not in classes(root.findall('.//thead/tr/th')[1])

    # Now try with an ordered table
    table = SimpleTable([], order_by='a')
    root = parse(table.as_html(request))
    # return classes of an element as a set
    assert 'orderable' in classes(root.findall('.//thead/tr/th')[0])
    assert 'asc' in classes(root.findall('.//thead/tr/th')[0])
    assert 'orderable' not in classes(root.findall('.//thead/tr/th')[1])


def test_empty_values_triggers_default():
    class Table(tables.Table):
        a = tables.Column(empty_values=(1, 2), default='--')

    table = Table([{'a': 1}, {'a': 2}, {'a': 3}, {'a': 4}])
    assert [row.get_cell('a') for row in table.rows] == ['--', '--', 3, 4]


def test_register_skips_non_columns():
    from django_tables2.columns.base import library

    @library.register
    class Klass(object):
        pass

    class Table(tables.Table):
        class Meta:
            model = Person

    Table([])


def test_raises_when_using_non_supported_index():
    class Table(tables.Table):
        column = tables.Column()

    table = Table([{'column': 'foo'}])

    row = table.rows[0]
    with pytest.raises(TypeError):
        row[table]


class MyModel(models.Model):
    item1 = models.CharField(max_length=10)

    class Meta:
        app_label = 'django_tables2_tests'


class MyTable(tables.Table):
    item1 = tables.Column(verbose_name='Nice column name')

    class Meta:
        model = MyModel
        fields = ('item1', )


def test_column_params_should_be_preserved_under_inheritance():
    '''
    Github issue #337

    Columns explicitly defined on MyTable get overridden by columns implicitly
    defined on it's child.
    If the column is not redefined, the explicit definition of MyTable is used,
    preserving the specialized verbose_name defined on it.
    '''

    class MyTableA(MyTable):
        '''
        having an empty `class Meta` should not undo the explicit definition
        of column item1 in MyTable.
        '''
        class Meta(MyTable.Meta):
            pass

    class MyTableB(MyTable):
        '''
        having a non-empty `class Meta` should not undo the explicit definition
        of column item1 in MyTable.
        '''
        class Meta(MyTable.Meta):
            per_page = 22

    table = MyTable(MyModel.objects.all())
    tableA = MyTableA(MyModel.objects.all())
    tableB = MyTableB(MyModel.objects.all())

    assert table.columns['item1'].verbose_name == 'Nice column name'
    assert tableA.columns['item1'].verbose_name == 'Nice column name'
    assert tableB.columns['item1'].verbose_name == 'Nice column name'


def test_explicit_column_can_be_overridden_by_other_explicit_column():
    class MyTableC(MyTable):
        '''
        If we define a new explict item1 column, that one should be used.
        '''
        item1 = tables.Column(verbose_name='New nice column name')

    table = MyTable(MyModel.objects.all())
    tableC = MyTableC(MyModel.objects.all())

    assert table.columns['item1'].verbose_name == 'Nice column name'
    assert tableC.columns['item1'].verbose_name == 'New nice column name'


def test_override_column_class_names():
    '''
    We control the output of CSS class names for a column by overriding
    get_column_class_names
    '''
    class MyTable(tables.Table):
        population = tables.Column(verbose_name='Population')

        def get_column_class_names(self, classes_set, bound_column):
            classes_set.add('prefix-%s' % bound_column.name)
            return classes_set

    TEST_DATA = [
        {'name': 'Belgium', 'population': 11200000},
        {'name': 'Luxembourgh', 'population': 540000},
        {'name': 'France', 'population': 66000000},
    ]

    html = MyTable(TEST_DATA).as_html(build_request())

    assert '<td class="prefix-population">11200000</td>' in html
