# coding: utf-8
from __future__ import absolute_import, unicode_literals

import pytest
from django.contrib.auth import get_user_model

import django_tables2 as tables
from .utils import build_request

User = get_user_model()

data = [
    {'name': 'Adrian', 'country': 'Australia'},
    {'name': 'Adrian', 'country': 'Brazil'},
    {'name': 'Audrey', 'country': 'Chile'},
    {'name': 'Bassie', 'country': 'Belgium'},
]


def test_dynamically_adding_columns():
    '''
    When adding columns to self.base_columns, they are actually added to
    the class attribute `Table.base_columns`, and not to the instance
    attribute, `table.base_columns`

    issue #403
    '''
    class MyTable(tables.Table):
        name = tables.Column()

    # this is obvious:
    assert list(MyTable(data).columns.columns.keys()) == ['name']

    assert list(MyTable(data, extra_columns=[
        ('country', tables.Column())
    ]).columns.columns.keys()) == ['name', 'country']

    # this new instance should not have the extra columns added to the first instance.
    assert list(MyTable(data).columns.columns.keys()) == ['name']


@pytest.mark.django_db
def test_dynamically_hide_columns():
    class MyTable(tables.Table):
        name = tables.Column(orderable=False)
        country = tables.Column(orderable=False)

        def before_render(self, request):
            if request.user.username == 'Bob':
                self.columns.hide('country')
            else:
                self.columns.show('country')

    table = MyTable(data)
    html = table.as_html(build_request(user=User.objects.create(username='Bob')))
    assert '<th class="name">Name</th>' in html
    assert '<th class="country">Country</th>' not in html

    html = table.as_html(build_request(user=User.objects.create(username='Alice')))
    assert '<th class="name">Name</th>' in html
    assert '<th class="country">Country</th>' in html
