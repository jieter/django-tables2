# coding: utf-8
import pytest
from django.core.exceptions import ImproperlyConfigured
from django.views.generic.base import TemplateView

import django_tables2 as tables

from .app.models import Person, Region
from .utils import build_request

MEMORY_DATA = [
    {'name': 'Queensland'},
    {'name': 'New South Wales'},
    {'name': 'Victoria'},
    {'name': 'Tasmania'}
]


class DispatchHookMixin(object):
    """
    Returns a response *and* reference to the view.
    """
    def dispatch(self, *args, **kwargs):
        return super(DispatchHookMixin, self).dispatch(*args, **kwargs), self


class SimpleTable(tables.Table):
    class Meta:
        model = Region


class SimpleView(DispatchHookMixin, tables.SingleTableView):
    table_class = SimpleTable
    table_pagination = {'per_page': 1}
    model = Region  # needed for ListView


@pytest.mark.django_db
def test_view_should_support_pagination_options():
    for region in MEMORY_DATA:
        Region.objects.create(name=region['name'])

    response, view = SimpleView.as_view()(build_request('/'))
    assert view.get_table().paginator.num_pages == len(MEMORY_DATA)


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
    class ExplicitDataView(SimpleView):
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
    assert view.get_table().paginator.num_pages == 2


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
    assert view.get_table().paginator.num_pages == 2


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


@pytest.mark.django_db
def test_multiTableMixin_basic():
    Person.objects.create(first_name='Jan Pieter', last_name='W')

    Region.objects.create(name='Zuid-Holland')
    Region.objects.create(name='Noord-Holland')

    class TableA(tables.Table):
        class Meta:
            model = Person

    class TableB(tables.Table):
        class Meta:
            model = Region
            exclude = ('id', )

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

    class TableA(tables.Table):
        class Meta:
            model = Person

    class TableB(tables.Table):
        class Meta:
            model = Region
            exclude = ('id', )

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
    class TableA(tables.Table):
        class Meta:
            model = Person

    class TableB(tables.Table):
        class Meta:
            model = Region
            exclude = ('id', )

    class View(tables.MultiTableMixin, TemplateView):
        tables = (TableA, TableB)
        tables_data = (Person.objects.all(), )
        template_name = 'multiple.html'

    with pytest.raises(ImproperlyConfigured):
        View.as_view()(build_request('/'))
