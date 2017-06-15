# coding: utf-8
from __future__ import absolute_import, unicode_literals

import pytest
from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.utils.translation import ugettext as _
import django_tables2 as tables

from django_tables2.config import RequestConfig
from django.template.defaultfilters import date as _date
from .app.models import Person, ActivityType, Activity
from .utils import build_request

User = get_user_model()

data = [
    {'name': 'Adrian', 'country': 'Australia'},
    {'name': 'Adrian', 'country': 'Brazil'},
    {'name': 'Audrey', 'country': 'Chile'},
    {'name': 'Bassie', 'country': 'Belgium'},
]

activity_types_data = [
    'testing',
    'trying'
]

activities_data = [
   '2017-06-15',
   '2017-06-15'
]


def test_dynamically_adding_columns():
    '''
    When adding columns to self.base_columns, they were actually added to
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
def test_dynamically_override_auto_generated_columns():
    for name, country in data:
        Person.objects.create(first_name=name, last_name=country)
    queryset = Person.objects.all()

    class MyTable(tables.Table):
        class Meta:
            model = Person
            fields = ('first_name', 'last_name')

    assert list(MyTable(queryset).columns.columns.keys()) == ['first_name', 'last_name']

    table = MyTable(queryset, extra_columns=[
        ('first_name', tables.Column(attrs={'td': {'style': 'color: red;'}}))
    ])
    # we still should have two columns
    assert list(table.columns.columns.keys()) == ['first_name', 'last_name']
    # the attrs should be applied to the `first_name` column
    assert table.columns['first_name'].attrs['td'] == {'class': 'first_name', 'style': 'color: red;'}


def test_dynamically_add_column_with_sequence():
    class MyTable(tables.Table):
        name = tables.Column()

        class Meta:
            sequence = ('...', 'name')

    assert list(MyTable(data, extra_columns=[
        ('country', tables.Column())
    ]).columns.columns.keys()) == ['country', 'name']

    # override sequence with an argument.
    assert list(MyTable(
        data,
        extra_columns=[('country', tables.Column())],
        sequence=('name', '...')
    ).columns.columns.keys()) == ['name', 'country']


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

    template = Template('{% load django_tables2 %}{% render_table table %}')

    table = MyTable(data)
    request = build_request(user=User.objects.create(username='Bob'))
    html = table.as_html(request)
    assert '<th class="name">Name</th>' in html
    assert '<th class="country">Country</th>' not in html

    html = template.render(Context({'request': request, 'table': table}))
    assert '<th class="name">Name</th>' in html
    assert '<th class="country">Country</th>' not in html

    request = build_request(user=User.objects.create(username='Alice'))
    html = table.as_html(request)
    assert '<th class="name">Name</th>' in html
    assert '<th class="country">Country</th>' in html

    html = template.render(Context({'request': request, 'table': table}))
    assert '<th class="name">Name</th>' in html
    assert '<th class="country">Country</th>' in html



@pytest.mark.django_db
def test_extra_columns_with_custom_column_render():

    for name, country in data:
        Person.objects.create(first_name=name, last_name=country)
    queryset = Person.objects.all()

    for name in activity_types_data:
        ActivityType.objects.create(name=name)

    for date in activities_data:
        Activity.objects.create(activity_type_id=1, date=date, person_id=1)



    class MyColumn(tables.Column):
        empty_values = ()
        def __init__(self, *args, **kwargs):
            self.activity_type = kwargs.pop('activity_type')
            super(MyColumn, self).__init__(*args, **kwargs)
        def render(self,record, table, value, bound_column, **kwargs):     
            activity = record.last_for_activity_type(self.activity_type) 
            if activity:
                value = _date(activity.date, "DATE_FORMAT")
            else:
                value = '—'
            return value

    class MyTable(tables.Table):
        class Meta:
            model = Person
            fields = ('name',)
            sequence = ('name', '...')

    extra_columns = ()
    extra_columns += tuple([('last_{}'.format(x.name.replace(" ", "_")), MyColumn(activity_type=x, verbose_name=_('Last {}').format(x.name))) for x in ActivityType.objects.all()])

    table = MyTable(queryset, extra_columns=extra_columns)
    template = Template('{% load django_tables2 %}{% render_table table %}')

    request = build_request(user=User.objects.create(username='Bob'))
    RequestConfig(request).configure(table)
    html = template.render(Context({'request': request, 'table': table}))

    assert 'last_testing' in html
