# coding: utf-8
import django_tables2 as tables
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import TemplateView

import pytest

from .app.models import Person, Region
from .utils import build_request

MEMORY_DATA = [
    {'name': 'Queensland'},
    {'name': 'New South Wales'},
    {'name': 'Victoria'},
    {'name': 'Tasmania'}
]


class DispatchHookMixin(object):
    '''
    Returns a response *and* reference to the view.
    '''
    def dispatch(self, *args, **kwargs):
        return super(DispatchHookMixin, self).dispatch(*args, **kwargs), self


class SimpleTable(tables.Table):
    class Meta:
        model = Region


class SimpleView(DispatchHookMixin, tables.SingleTableView):
    table_class = SimpleTable
    model = Region  # required for ListView


class SimplePaginatedView(DispatchHookMixin, tables.SingleTableView):
    table_class = SimpleTable
    table_pagination = {'per_page': 1}
    model = Region  # required for ListView


@pytest.mark.django_db
def test_view_should_support_pagination_options():
    for region in MEMORY_DATA:
        Region.objects.create(name=region['name'])

    response, view = SimplePaginatedView.as_view()(build_request('/'))
    assert view.get_table().paginator.num_pages == len(MEMORY_DATA)
    assert view.get_table().paginator.per_page == 1


@pytest.mark.django_db
def test_view_should_support_default_pagination():
    class PaginateDefault(DispatchHookMixin, tables.SingleTableView):
        table_class = SimpleTable
        model = Region
        table_data = MEMORY_DATA

    response, view = PaginateDefault.as_view()(build_request('/'))
    table = view.get_table()
    assert table.paginator.per_page == 25
    assert len(table.page) == 4


@pytest.mark.django_db
def test_view_should_support_default_pagination_with_table_options():
    class Table(tables.Table):
        class Meta:
            model = Region
            per_page = 2

    class PaginateByDefinedOnView(DispatchHookMixin, tables.SingleTableView):
        table_class = Table
        model = Region
        table_data = MEMORY_DATA

    response, view = PaginateByDefinedOnView.as_view()(build_request('/'))
    table = view.get_table()
    assert table.paginator.per_page == 2
    assert len(table.page) == 2


@pytest.mark.django_db
def test_view_should_support_disabling_pagination_options():
    class SimpleNotPaginatedView(DispatchHookMixin, tables.SingleTableView):
        table_class = SimpleTable
        table_data = MEMORY_DATA
        table_pagination = False
        model = Region  # required for ListView

    response, view = SimpleNotPaginatedView.as_view()(build_request('/'))
    table = view.get_table()
    assert not hasattr(table, 'page')


@pytest.mark.django_db
def test_view_from_get_queryset():
    for region in MEMORY_DATA:
        Region.objects.create(name=region['name'])

    class GetQuerysetView(SimpleView):
        def get_queryset(self):
            return Region.objects.filter(name__startswith='Q')

    response, view = GetQuerysetView.as_view()(build_request('/'))
    table = view.get_table()

    assert len(table.rows) == 1
    assert table.rows[0].get_cell('name') == 'Queensland'


def test_should_raise_without_tableclass():
    class WithoutTableclassView(tables.SingleTableView):
        model = Region

    with pytest.raises(ImproperlyConfigured):
        WithoutTableclassView.as_view()(build_request('/'))


def test_should_support_explicit_table_data():
    class ExplicitDataView(SimplePaginatedView):
        table_data = MEMORY_DATA

    response, view = ExplicitDataView.as_view()(build_request('/'))
    assert view.get_table().paginator.num_pages == len(MEMORY_DATA)


@pytest.mark.django_db
def test_paginate_by_on_view_class():
    class Table(tables.Table):
        class Meta:
            model = Region

    class PaginateByDefinedOnView(DispatchHookMixin, tables.SingleTableView):
        table_class = Table
        model = Region
        paginate_by = 2
        table_data = MEMORY_DATA

    response, view = PaginateByDefinedOnView.as_view()(build_request('/'))
    assert view.get_table().paginator.per_page == 2


@pytest.mark.django_db
def test_should_pass_kwargs_to_table_constructor():

    class PassKwargsView(SimpleView):
        table_data = []

        def get_table(self, **kwargs):
            kwargs.update({'orderable': False})
            return super(PassKwargsView, self).get_table(**kwargs)

    response, view = SimpleView.as_view()(build_request('/'))
    assert view.get_table().orderable is True

    response, view = PassKwargsView.as_view()(build_request('/'))
    assert view.get_table().orderable is False


@pytest.mark.django_db
def test_should_override_table_pagination():

    class PrefixedTable(SimpleTable):
        class Meta(SimpleTable.Meta):
            prefix = 'p_'

    class PrefixedView(SimpleView):
        table_class = PrefixedTable

    class PaginationOverrideView(PrefixedView):
        table_data = MEMORY_DATA

        def get_table_pagination(self, table):
            assert isinstance(table, tables.Table)

            per_page = self.request.GET.get('%s_override' % table.prefixed_per_page_field)
            if per_page is not None:
                return {'per_page': per_page}
            return super(PaginationOverrideView, self).get_table_pagination(table)

    response, view = PaginationOverrideView.as_view()(build_request('/?p_per_page_override=2'))
    assert view.get_table().paginator.per_page == 2


def test_singletablemixin_with_non_paginated_view():
    '''
    SingleTableMixin should not assume it is mixed with a ListView

    Github issue #326
    '''

    class Table(tables.Table):
        class Meta:
            model = Region

    class View(tables.SingleTableMixin, TemplateView):
        table_class = Table
        table_data = MEMORY_DATA

        template_name = 'dummy.html'

    View.as_view()(build_request('/'))


class TableA(tables.Table):
    class Meta:
        model = Person


class TableB(tables.Table):
    class Meta:
        model = Region
        exclude = ('id', )


@pytest.mark.django_db
def test_multiTableMixin_basic():
    Person.objects.create(first_name='Jan Pieter', last_name='W')

    Region.objects.create(name='Zuid-Holland')
    Region.objects.create(name='Noord-Holland')

    class View(tables.MultiTableMixin, TemplateView):
        tables = (TableA, TableB)
        tables_data = (Person.objects.all(), Region.objects.all())
        template_name = 'multiple.html'

    response = View.as_view()(build_request('/'))
    response.render()

    html = response.rendered_content

    assert 'table_0-sort=first_name' in html
    assert 'table_1-sort=name' in html

    assert '<td class="first_name">Jan Pieter</td>' in html
    assert '<td class="name">Zuid-Holland</td>' in html


@pytest.mark.django_db
def test_multiTableMixin_basic_alternative():
    Person.objects.create(first_name='Jan Pieter', last_name='W')

    Region.objects.create(name='Zuid-Holland')
    Region.objects.create(name='Noord-Holland')

    class View(tables.MultiTableMixin, TemplateView):
        tables = (
            TableA(Person.objects.all()),
            TableB(Region.objects.all())
        )
        template_name = 'multiple.html'

    response = View.as_view()(build_request('/'))
    response.render()

    html = response.rendered_content

    assert 'table_0-sort=first_name' in html
    assert 'table_1-sort=name' in html

    assert '<td class="first_name">Jan Pieter</td>' in html
    assert '<td class="name">Zuid-Holland</td>' in html


def test_multiTableMixin_without_tables():
    class View(tables.MultiTableMixin, TemplateView):
        template_name = 'multiple.html'

    with pytest.raises(ImproperlyConfigured):
        View.as_view()(build_request('/'))


def test_multiTableMixin_incorrect_len():

    class View(tables.MultiTableMixin, TemplateView):
        tables = (TableA, TableB)
        tables_data = (Person.objects.all(), )
        template_name = 'multiple.html'

    with pytest.raises(ImproperlyConfigured):
        View.as_view()(build_request('/'))


@pytest.mark.django_db
def test_multiTableMixin_pagination():
    NL_PROVICES = (
        'Flevoland', 'Friesland', 'Gelderland', 'Groningen', 'Limburg',
        'Noord-Brabant', 'Noord-Holland', 'Overijssel', 'Utrecht',
        'Zeeland', 'Zuid-Holland',
    )
    for name in NL_PROVICES:
        Region.objects.create(name=name)

    class View(DispatchHookMixin, tables.MultiTableMixin, TemplateView):
        tables = (
            TableB(Region.objects.all()),
            TableB(Region.objects.all())
        )
        template_name = 'multiple.html'

        table_pagination = {
            'per_page': 5
        }

    response, view = View.as_view()(build_request('/?table_1-page=3'))

    tableA, tableB = view.get_tables()

    assert tableA.page.number == 1
    assert tableB.page.number == 3


@pytest.mark.django_db
def test_View_using_get_queryset():
    '''
    Should not raise a value-error for a View using View.get_queryset()
    (test for reverting regressing in #423)
    '''
    Person.objects.create(first_name='Anton', last_name='Sam')

    class Table(tables.Table):
        class Meta(object):
            model = Person
            fields = ('first_name', 'last_name')

    class TestView(tables.SingleTableView):
        model = Person
        table_class = Table

        def get(self, request, *args, **kwargs):
            self.get_table()
            from django.http import HttpResponse
            return HttpResponse()

        def get_queryset(self):
            '''get_queryset should be called'''
            return Person.objects.all()

    TestView.as_view()(build_request())
