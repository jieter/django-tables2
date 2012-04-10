# -*- coding: utf-8 -*-
from .app.models import Region
from attest import assert_hook, Assert, Tests
from django_attest import TestContext
from django.test.client import RequestFactory
import django_tables2 as tables


views = Tests()
views.context(TestContext())


class DispatchHookMixin(object):
    """
    Returns a response *and* reference to the view.
    """
    def dispatch(self, *args, **kwargs):
        return super(DispatchHookMixin, self).dispatch(*args, **kwargs), self


class SimpleTable(tables.Table):
    class Meta:
        model = Region


@views.test
def view_should_support_pagination_options():
    for name in ("Queensland", "New South Wales", "Victoria", "Tasmania"):
        Region.objects.create(name=name)


    class SimpleView(DispatchHookMixin, tables.SingleTableView):
        table_class = SimpleTable
        table_pagination = {"per_page": 1}
        model = Region  # needed for ListView

    request = RequestFactory().get('/')
    response, view = SimpleView.as_view()(request)
    assert view.get_table().paginator.num_pages == 4


@views.test
def should_support_explicit_table_data():
    class SimpleView(DispatchHookMixin, tables.SingleTableView):
        table_class = SimpleTable
        table_data = [
            {"name": "Queensland"},
            {"name": "New South Wales"},
            {"name": "Victoria"},
        ]
        table_pagination = {"per_page": 1}
        model = Region  # needed for ListView

    request = RequestFactory().get('/')
    response, view = SimpleView.as_view()(request)
    assert view.get_table().paginator.num_pages == 3
