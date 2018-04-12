# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.contrib.auth import get_user_model
from django.template import Context, Template
from django.test import TestCase
from django.utils.translation import ugettext_lazy as _

import django_tables2 as tables

from .app.models import Person
from .utils import build_request, parse

User = get_user_model()

data = [
    {'name': 'Adrian', 'country': 'Australia'},
    {'name': 'Roy', 'country': 'Brazil'},
    {'name': 'Audrey', 'country': 'Chile'},
    {'name': 'Bassie', 'country': 'Belgium'},
]


class DynamicColumnsTest(TestCase):
    def test_dynamically_adding_columns(self):
        '''
        When adding columns to self.base_columns, they were actually added to
        the class attribute `Table.base_columns`, and not to the instance
        attribute, `table.base_columns`

        issue #403
        '''
        class MyTable(tables.Table):
            name = tables.Column()

        # this is obvious:
        self.assertEqual(list(MyTable(data).columns.columns.keys()), ['name'])

        self.assertEqual(list(MyTable(data, extra_columns=[
            ('country', tables.Column())
        ]).columns.columns.keys()), ['name', 'country'])

        # this new instance should not have the extra columns added to the first instance.
        self.assertEqual(list(MyTable(data).columns.columns.keys()), ['name'])

    def test_dynamically_removing_columns(self):
        class MyTable(tables.Table):
            name = tables.Column()

        # this is obvious:
        self.assertEqual(list(MyTable(data).columns.columns.keys()), ['name'])

        self.assertEqual(list(MyTable(data, extra_columns=[
            ('country', tables.Column()),
            ('name', None)
        ]).columns.columns.keys()), ['country'])

        # this new instance should not have the extra columns added to the first instance.
        self.assertEqual(list(MyTable(data).columns.columns.keys()), ['name'])

    def test_sorting_on_dynamically_added_columns(self):
        class MyTable(tables.Table):
            name = tables.Column()

        table = MyTable(data, order_by='-country', extra_columns=[
            ('country', tables.Column(verbose_name=_('country')))
        ])

        root = parse(table.as_html(build_request()))
        self.assertEqual(root.find('.//tbody/tr/td[2]').text, 'Chile')
        self.assertEqual(root.find('.//tbody/tr[4]/td[2]').text, 'Australia')

    def test_dynamically_override_auto_generated_columns(self):
        for name, country in data:
            Person.objects.create(first_name=name, last_name=country)
        queryset = Person.objects.all()

        class MyTable(tables.Table):
            class Meta:
                model = Person
                fields = ('first_name', 'last_name')

        self.assertEqual(list(MyTable(queryset).columns.columns.keys()), ['first_name', 'last_name'])

        table = MyTable(queryset, extra_columns=[
            ('first_name', tables.Column(attrs={'td': {'style': 'color: red;'}}))
        ])
        # we still should have two columns
        self.assertEqual(list(table.columns.columns.keys()), ['first_name', 'last_name'])
        # the attrs should be applied to the `first_name` column
        self.assertEqual(table.columns['first_name'].attrs['td'], {'style': 'color: red;', 'class': None})

    def test_dynamically_add_column_with_sequence(self):
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

    def test_dynamically_hide_columns(self):
        class MyTable(tables.Table):
            name = tables.Column(orderable=False)
            country = tables.Column(orderable=False)

            def before_render(self, request):
                if request.user.username == 'Bob':
                    self.columns.hide('country')
                else:
                    self.columns.show('country')

        template = Template('{% load django_tables2 %}{% render_table table %}')

        re_Name = r'<th >\s*Name\s*</th>'
        re_Country = r'<th >\s*Country\s*</th>'

        table = MyTable(data)
        request = build_request(user=User.objects.create(username='Bob'))
        html = table.as_html(request)
        self.assertRegexpMatches(html, re_Name)
        self.assertNotRegexpMatches(html, re_Country)

        html = template.render(Context({'request': request, 'table': table}))
        self.assertRegexpMatches(html, re_Name)
        self.assertNotRegexpMatches(html, re_Country)

        request = build_request(user=User.objects.create(username='Alice'))
        html = table.as_html(request)
        self.assertRegexpMatches(html, re_Name)
        self.assertRegexpMatches(html, re_Country)

        html = template.render(Context({'request': request, 'table': table}))
        self.assertRegexpMatches(html, re_Name)
        self.assertRegexpMatches(html, re_Country)
