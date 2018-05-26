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

    # shim can be dropped when we drop support for python 2.7 and 3.4
    if not hasattr(TestCase, 'assertRegex'):
        assertRegex = TestCase.assertRegexpMatches
    if not hasattr(TestCase, 'assertNotRegex'):
        assertNotRegex = TestCase.assertNotRegexpMatches

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

        self.assertEqual(list(MyTable(data, extra_columns=[
            ('country', tables.Column())
        ]).columns.columns.keys()), ['country', 'name'])

        # override sequence with an argument.
        self.assertEqual(list(MyTable(
            data,
            extra_columns=[('country', tables.Column())],
            sequence=('name', '...')
        ).columns.columns.keys()), ['name', 'country'])

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
        self.assertRegex(html, re_Name)
        self.assertNotRegex(html, re_Country)

        html = template.render(Context({'request': request, 'table': table}))
        self.assertRegex(html, re_Name)
        self.assertNotRegex(html, re_Country)

        request = build_request(user=User.objects.create(username='Alice'))
        html = table.as_html(request)
        self.assertRegex(html, re_Name)
        self.assertRegex(html, re_Country)

        html = template.render(Context({'request': request, 'table': table}))
        self.assertRegex(html, re_Name)
        self.assertRegex(html, re_Country)

    def test_sequence_and_extra_columns(self):
        """
        https://github.com/jieter/django-tables2/issues/486

        The exact moment the '...' is expanded is crucial here.
        """

        add_occupation_column = True

        class MyTable(tables.Table):

            class Meta:
                model = Person
                fields = ('first_name', 'friends',)
                sequence = ('first_name', '...', 'friends')

            def __init__(self, data, *args, **kwargs):
                kwargs['extra_columns'] = kwargs.get('extra_columns', [])

                if add_occupation_column:
                    kwargs['extra_columns'].append(
                        ('occupation', tables.RelatedLinkColumn(orderable=False,))
                    )

                super(MyTable, self).__init__(data, *args, **kwargs)

        table = MyTable(Person.objects.all())
        self.assertEqual([c.name for c in table.columns], ['first_name', 'occupation', 'friends'])

        add_occupation_column = False
        table = MyTable(Person.objects.all())
        self.assertEqual([c.name for c in table.columns], ['first_name', 'friends'])

    def test_change_attributes(self):
        """
        https://github.com/jieter/django-tables2/issues/574
        """

        class Table(tables.Table):
            mycolumn = tables.Column(orderable=False)

            def __init__(self, *args, **kwargs):
                self.base_columns['mycolumn'].verbose_name = 'Monday'
                super(Table, self).__init__(*args, **kwargs)

        table = Table([])
        self.assertEqual(table.columns['mycolumn'].verbose_name, 'Monday')
