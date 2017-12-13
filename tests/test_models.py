# coding: utf-8
from __future__ import unicode_literals

from collections import defaultdict
from unittest import mock

import pytest
from django.db.models.functions import Length
from django.utils import six
from django.utils.translation import override as translation_override

import django_tables2 as tables

from .app.models import Occupation, Person, PersonProxy
from .utils import assertNumQueries, build_request

pytestmark = pytest.mark.django_db
request = build_request('/')


class PersonTable(tables.Table):
    first_name = tables.Column()
    last_name = tables.Column()
    occupation = tables.Column()


def test_boundrows_iteration():
    occupation = Occupation.objects.create(name='Programmer')
    Person.objects.create(first_name='Bradley', last_name='Ayers', occupation=occupation)
    Person.objects.create(first_name='Chris', last_name='Doble', occupation=occupation)

    table = PersonTable(Person.objects.all())
    records = [row.record for row in table.rows]
    expecteds = Person.objects.all()
    for expected, actual in six.moves.zip(expecteds, records):
        assert expected == actual


def test_model_table():
    '''
    The ``model`` option on a table causes the table to dynamically add columns
    based on the fields.
    '''
    class OccupationTable(tables.Table):
        class Meta:
            model = Occupation

    expected = ['id', 'name', 'region', 'boolean', 'boolean_with_choices']
    assert expected == list(OccupationTable.base_columns.keys())

    class OccupationTable2(tables.Table):
        extra = tables.Column()

        class Meta:
            model = Occupation

    expected.append('extra')
    assert expected == list(OccupationTable2.base_columns.keys())

    # be aware here, we already have *models* variable, but we're importing
    # over the top
    from django.db import models

    class ComplexModel(models.Model):
        char = models.CharField(max_length=200)
        fk = models.ForeignKey('self', on_delete=models.CASCADE)
        m2m = models.ManyToManyField('self')

        class Meta:
            app_label = 'django_tables2_test'

    class ComplexTable(tables.Table):
        class Meta:
            model = ComplexModel
    assert ['id', 'char', 'fk'] == list(ComplexTable.base_columns.keys())


def test_mixins():
    class TableMixin(tables.Table):
        extra = tables.Column()

    class OccupationTable(TableMixin, tables.Table):
        extra2 = tables.Column()

        class Meta:
            model = Occupation

    expected = ['extra', 'id', 'name', 'region', 'boolean', 'boolean_with_choices', 'extra2']
    assert expected == list(OccupationTable.base_columns.keys())


def test_column_verbose_name():
    '''
    When using queryset data as input for a table, default to using model field
    verbose names rather than an autogenerated string based on the column name.

    However if a column does explicitly describe a verbose name, it should be
    used.
    '''
    class PersonTable(tables.Table):
        '''
        The test_colX columns are to test that the accessor is used to
        determine the field on the model, rather than the column name.
        '''
        first_name = tables.Column()
        fn1 = tables.Column(accessor='first_name')
        fn2 = tables.Column(accessor='first_name.upper')
        fn3 = tables.Column(accessor='last_name', verbose_name='OVERRIDE')
        fn4 = tables.Column(accessor='last_name', verbose_name='override')
        last_name = tables.Column()
        ln1 = tables.Column(accessor='last_name')
        ln2 = tables.Column(accessor='last_name.upper')
        ln3 = tables.Column(accessor='last_name', verbose_name='OVERRIDE')
        region = tables.Column(accessor='occupation.region.name')
        r1 = tables.Column(accessor='occupation.region.name')
        r2 = tables.Column(accessor='occupation.region.name.upper')
        r3 = tables.Column(accessor='occupation.region.name', verbose_name='OVERRIDE')
        trans_test = tables.Column()
        trans_test_lazy = tables.Column()

    # The Person model has a ``first_name`` and ``last_name`` field, but only
    # the ``last_name`` field has an explicit ``verbose_name`` set. This means
    # that we should expect that the two columns that use the ``last_name``
    # field should both use the model's ``last_name`` field's ``verbose_name``,
    # however both fields that use the ``first_name`` field should just use a
    # titlised version of the column name as the column header.
    table = PersonTable(Person.objects.all())

    # Should be generated (capitalized column name)
    assert 'First Name' == table.columns['first_name'].verbose_name
    assert 'First Name' == table.columns['fn1'].verbose_name
    assert 'First Name' == table.columns['fn2'].verbose_name
    assert 'OVERRIDE' == table.columns['fn3'].verbose_name
    assert 'override' == table.columns['fn4'].verbose_name
    # Should use the titlised model field's verbose_name
    assert 'Surname' == table.columns['last_name'].verbose_name
    assert 'Surname' == table.columns['ln1'].verbose_name
    assert 'Surname' == table.columns['ln2'].verbose_name
    assert 'OVERRIDE' == table.columns['ln3'].verbose_name
    assert 'Name' == table.columns['region'].verbose_name
    assert 'Name' == table.columns['r1'].verbose_name
    assert 'Name' == table.columns['r2'].verbose_name
    assert 'OVERRIDE' == table.columns['r3'].verbose_name
    assert 'Translation Test' == table.columns['trans_test'].verbose_name
    assert 'Translation Test Lazy' == table.columns['trans_test_lazy'].verbose_name

    # -------------------------------------------------------------------------

    # Now we'll try using a table with Meta.model
    class PersonTable(tables.Table):
        first_name = tables.Column(verbose_name='OVERRIDE')

        class Meta:
            model = Person

    # Issue #16
    table = PersonTable(Person.objects.all())
    assert 'Translation Test' == table.columns['trans_test'].verbose_name
    assert 'Translation Test Lazy' == table.columns['trans_test_lazy'].verbose_name
    assert 'Web Site' == table.columns['website'].verbose_name
    assert 'Birthdate' == table.columns['birthdate'].verbose_name
    assert 'OVERRIDE' == table.columns['first_name'].verbose_name

    # Verbose name should be lazy if it comes from the model field and
    # the column was not declared explicitly
    class PersonTable(tables.Table):
        class Meta:
            model = Person

    table = PersonTable(Person.objects.all())
    assert type(table.columns['trans_test_lazy'].verbose_name) is not six.text_type
    with translation_override('ua'):
        assert 'Тест Ленивого Перекладу' == table.columns['trans_test_lazy'].verbose_name


def test_data_verbose_name():
    table = tables.Table(Person.objects.all())
    assert table.data.verbose_name == 'person'
    assert table.data.verbose_name_plural == 'people'


def test_field_choices_used_to_translated_value():
    '''
    When a model field uses the ``choices`` option, a table should render the
    'pretty' value rather than the database value.

    See issue #30 for details.
    '''
    LANGUAGES = (
        ('en', 'English'),
        ('ru', 'Russian'),
    )

    from django.db import models

    class Article(models.Model):
        name = models.CharField(max_length=200)
        language = models.CharField(max_length=200, choices=LANGUAGES)

        class Meta:
            app_label = 'django_tables2_test'

        def __unicode__(self):
            return self.name

    class ArticleTable(tables.Table):
        class Meta:
            model = Article

    table = ArticleTable([Article(name='English article', language='en'),
                          Article(name='Russian article', language='ru')])

    assert 'English' == table.rows[0].get_cell('language')
    assert 'Russian' == table.rows[1].get_cell('language')


def test_column_mapped_to_nonexistant_field():
    '''
    Issue #9 describes how if a Table has a column that has an accessor that
    targets a non-existent field, a FieldDoesNotExist error is raised.
    '''
    class FaultyPersonTable(PersonTable):
        missing = tables.Column()

    table = FaultyPersonTable(Person.objects.all())
    table.as_html(request)  # the bug would cause this to raise FieldDoesNotExist


def test_should_support_rendering_multiple_times():
    class MultiRenderTable(tables.Table):
        name = tables.Column()

    # test queryset data
    table = MultiRenderTable(Person.objects.all())
    assert table.as_html(request) == table.as_html(request)


def test_ordering():
    class SimpleTable(tables.Table):
        name = tables.Column(order_by=('first_name', 'last_name'))

    table = SimpleTable(Person.objects.all(), order_by='name')
    assert table.as_html(request)


def test_default_order():
    '''
    If orderable=False, do not sort queryset.
    https://github.com/bradleyayers/django-tables2/issues/204
    '''
    table = PersonTable(PersonProxy.objects.all())
    Person.objects.create(first_name='Foo', last_name='Bar')
    Person.objects.create(first_name='Bradley', last_name='Ayers')
    table.data.order_by([])

    assert list(table.rows[0])[1] == 'Ayers'


def test_fields_should_implicitly_set_sequence():
    class PersonTable(tables.Table):
        extra = tables.Column()

        class Meta:
            model = Person
            fields = ('last_name', 'first_name')
    table = PersonTable(Person.objects.all())
    assert table.columns.names() == ['last_name', 'first_name', 'extra']


def test_model_properties_should_be_useable_for_columns():
    class PersonTable(tables.Table):
        class Meta:
            model = Person
            fields = ('name', 'first_name')

    Person.objects.create(first_name='Bradley', last_name='Ayers')
    table = PersonTable(Person.objects.all())
    assert list(table.rows[0]) == ['Bradley Ayers', 'Bradley']


def test_meta_fields_may_be_list():
    class PersonTable(tables.Table):
        class Meta:
            model = Person
            fields = ['name', 'first_name']

    Person.objects.create(first_name='Bradley', last_name='Ayers')
    table = PersonTable(Person.objects.all())
    assert list(table.rows[0]) == ['Bradley Ayers', 'Bradley']


def test_column_with_delete_accessor_shouldnt_delete_records():
    class PersonTable(tables.Table):
        delete = tables.Column()

    Person.objects.create(first_name='Bradley', last_name='Ayers')
    table = PersonTable(Person.objects.all())
    table.as_html(request)
    assert Person.objects.get(first_name='Bradley')


def test_order_by_derived_from_queryset():
    queryset = Person.objects.order_by('first_name', 'last_name', '-occupation__name')

    class PersonTable(tables.Table):
        name = tables.Column(order_by=('first_name', 'last_name'))
        occupation = tables.Column(order_by=('occupation__name',))

    assert PersonTable(
        queryset.order_by('first_name', 'last_name', '-occupation__name')
    ).order_by == ('name', '-occupation')

    class PersonTable(PersonTable):
        class Meta:
            order_by = ('occupation', )

    assert PersonTable(queryset.all()).order_by == ('occupation', )


def test_queryset_table_data_supports_ordering():
    class Table(tables.Table):
        class Meta:
            model = Person

    for name in ('Bradley Ayers', 'Stevie Armstrong'):
        first_name, last_name = name.split()
        Person.objects.create(first_name=first_name, last_name=last_name)

    table = Table(Person.objects.all())
    assert table.rows[0].get_cell('first_name') == 'Bradley'
    table.order_by = '-first_name'
    assert table.rows[0].get_cell('first_name') == 'Stevie'


def test_queryset_table_data_supports_custom_ordering():
    class Table(tables.Table):
        class Meta:
            model = Person
            order_by = 'first_name'

        def order_first_name(self, queryset, is_descending):
            # annotate to order by length of first_name + last_name
            queryset = queryset.annotate(
                length=Length('first_name') + Length('last_name')
            ).order_by(('-' if is_descending else '') + 'length')
            return (queryset, True)

    for name in ('Bradley Ayers', 'Stevie Armstrong', 'VeryLongFirstName VeryLongLastName'):
        first_name, last_name = name.split()
        Person.objects.create(first_name=first_name, last_name=last_name)

    table = Table(Person.objects.all())

    # Shortest full names first
    assert table.rows[0].get_cell('first_name') == 'Bradley'

    # Longest full names first
    table.order_by = '-first_name'
    assert table.rows[0].get_cell('first_name') == 'VeryLongFirstName'


def test_doesnotexist_from_accessor_should_use_default():
    class Table(tables.Table):
        class Meta:
            model = Person
            default = 'abc'
            fields = ('first_name', 'last_name', 'region')

    Person.objects.create(first_name='Brad', last_name='Ayers')

    table = Table(Person.objects.all())
    assert table.rows[0].get_cell('first_name') == 'Brad'
    assert table.rows[0].get_cell('region') == 'abc'


def test_unicode_field_names():
    class Table(tables.Table):
        class Meta:
            model = Person
            fields = (six.text_type('first_name'), )

    Person.objects.create(first_name='Brad')

    table = Table(Person.objects.all())
    assert table.rows[0].get_cell('first_name') == 'Brad'


def test_foreign_key():
    class PersonTable(tables.Table):
        class Meta:
            model = Person
            fields = ('foreign_key', )

    # TODO: implement


def test_fields_empty_list_means_no_fields():
    class Table(tables.Table):
        class Meta:
            model = Person
            fields = ()

    table = Table(Person.objects.all())
    assert len(table.columns.names()) == 0


def test_column_named_delete():
    class DeleteTable(tables.Table):
        delete = tables.TemplateColumn('[delete button]', verbose_name='')

        class Meta:
            model = Person
            fields = ('name', 'delete')

    person1 = Person.objects.create(first_name='Jan', last_name='Pieter')
    person2 = Person.objects.create(first_name='John', last_name='Peter')

    DeleteTable(Person.objects.all()).as_html(build_request())

    assert Person.objects.get(pk=person1.pk) == person1
    assert Person.objects.get(pk=person2.pk) == person2


def test_single_query_for_non_paginated_table():
    '''
    A non-paginated table should not generate a query for each row, but only
    one query fetch the rows.
    '''
    for i in range(10):
        Person.objects.create(first_name='Bob %d' % i, last_name='Builder')

    class PersonTable(tables.Table):
        class Meta:
            model = Person
            fields = ('first_name', 'last_name')
            order_by = ('last_name', 'first_name')

    table = PersonTable(Person.objects.all())

    with assertNumQueries(1):
        list(table.as_values())


def test_model__str__calls():
    '''
    Custom column introduces unnecessary calls to a model's __str__
    method
    '''
    calls = defaultdict(int)

    def counting__str__(self):
        calls[self.pk] += 1
        return self.first_name


    with mock.patch('tests.app.models.Person.__str__', counting__str__):
        for i in range(1, 4):
            Person.objects.create(first_name='Bob %d' % i, last_name='Builder')

        class PersonTable(tables.Table):
            class Meta:
                model = Person
                fields = ['first_name', 'last_name']

            edit = tables.Column()

        assert calls == {}

        table = PersonTable(Person.objects.all())
        html = table.as_html(build_request())

        assert calls == {}
