# coding: utf-8
from __future__ import unicode_literals

import json

import pytest
from django.core.exceptions import ImproperlyConfigured

import django_tables2 as tables
from django_tables2.export.views import ExportMixin

from ..app.models import Person
from ..test_views import DispatchHookMixin
from ..utils import build_request

NAMES = [
    ('Yildiz', 'van der Kuil'),
    ('Lindi', 'Hakvoort'),
    ('Gerardo', 'Castelein'),
]


def create_test_data():
    for first_name, last_name in NAMES:
        Person.objects.create(first_name=first_name, last_name=last_name)


class Table(tables.Table):
    first_name = tables.Column()
    last_name = tables.Column()


class View(DispatchHookMixin, ExportMixin, tables.SingleTableView):
    table_class = Table
    table_pagination = {'per_page': 1}
    model = Person  # required for ListView
    template_name = 'django_tables2/bootstrap.html'


@pytest.mark.django_db
def test_view_should_support_csv_export():
    create_test_data()
    expected = '\r\n'.join(
        ('First Name,Surname', 'Yildiz,van der Kuil', 'Lindi,Hakvoort', 'Gerardo,Castelein')
    ) + '\r\n'

    response, view = View.as_view()(build_request('/?_export=csv'))
    assert response.getvalue().decode('utf8') == expected

    # should just render the normal table without the _export query
    response, view = View.as_view()(build_request('/'))
    html = response.render().rendered_content

    assert 'Yildiz' in html
    assert 'Lindy' not in html


@pytest.mark.django_db
def test_view_should_support_json_export():
    create_test_data()

    expected = list([
        {'First Name': m.first_name, 'Surname': m.last_name}
        for m in Person.objects.all()
    ])

    response, view = View.as_view()(build_request('/?_export=json'))
    assert json.loads(response.getvalue().decode('utf8')) == expected
