# coding: utf-8
import pytest
from django.core.exceptions import ImproperlyConfigured

import django_tables2 as tables

from .app.models import Region
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
