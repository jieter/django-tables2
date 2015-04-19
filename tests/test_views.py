# coding: utf-8
from .app.models import Region
import django_tables2 as tables
from django_tables2.utils import build_request
import pytest


USING_CBV = hasattr(tables, "SingleTableView")


class DispatchHookMixin(object):
    """
    Returns a response *and* reference to the view.
    """
    def dispatch(self, *args, **kwargs):
        return super(DispatchHookMixin, self).dispatch(*args, **kwargs), self


class SimpleTable(tables.Table):
    class Meta:
        model = Region


@pytest.mark.skipif(not USING_CBV, reason="requires class based views")
@pytest.mark.django_db
def test_view_should_support_pagination_options():
    for name in ("Queensland", "New South Wales", "Victoria", "Tasmania"):
        Region.objects.create(name=name)

    class SimpleView(DispatchHookMixin, tables.SingleTableView):
        table_class = SimpleTable
        table_pagination = {"per_page": 1}
        model = Region  # needed for ListView

    request = build_request('/')
    response, view = SimpleView.as_view()(request)
    assert view.get_table().paginator.num_pages == 4


@pytest.mark.skipif(not USING_CBV, reason="requires class based views")
def test_should_support_explicit_table_data():
    class SimpleView(DispatchHookMixin, tables.SingleTableView):
        table_class = SimpleTable
        table_data = [
            {"name": "Queensland"},
            {"name": "New South Wales"},
            {"name": "Victoria"},
        ]
        table_pagination = {"per_page": 1}
        model = Region  # needed for ListView

    request = build_request('/')
    response, view = SimpleView.as_view()(request)
    assert view.get_table().paginator.num_pages == 3
