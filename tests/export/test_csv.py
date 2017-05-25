# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.core.exceptions import ImproperlyConfigured

import django_tables2 as tables
from django_tables2.export.views import ExportMixin

from ..app.models import Person
from ..test_views import DispatchHookMixin
from ..utils import build_request

NAMES = [
    'Heydər Əliyev',
    'འབྲུག་ཡུལ།',
    '中国',
    '⠋⠗⠁⠝⠉⠑'
]


class Table(tables.Table):
    first_name = tables.Column()


class View(DispatchHookMixin, ExportMixin, tables.SingleTableView):
    table_class = Table
    table_pagination = {'per_page': 1}
    model = Person  # required for ListView


@pytest.mark.django_db
def test_view_should_support_csv_export():
    for name in NAMES:
        Person.objects.create(first_name=name)

    response, view = View.as_view()(build_request('/?_export=csv'))

    response = view.create_export()
    print(response)
    # assert False
