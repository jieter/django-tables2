# -*- coding: utf-8 -*-
"""Test the core table functionality."""
from attest import Tests, Assert
from django.test.client import RequestFactory
from django.template import Context, Template
import django_tables as tables
from django_tables import utils, A


columns = Tests()


@columns.test
def sortable():
    class SimpleTable(tables.Table):
        name = tables.Column()
    Assert(SimpleTable([]).columns['name'].sortable) is True

    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            sortable = False
    Assert(SimpleTable([]).columns['name'].sortable) is False

    class SimpleTable(tables.Table):
        name = tables.Column()

        class Meta:
            sortable = True
    Assert(SimpleTable([]).columns['name'].sortable) is True


@columns.test
def link_column():
    """Test LinkColumn"""
    # test unicode values + headings
    class UnicodeTable(tables.Table):
        first_name = tables.LinkColumn('person', args=[A('pk')])
        last_name = tables.LinkColumn('person', args=[A('pk')], verbose_name=u'äÚ¨´ˆÁ˜¨ˆ˜˘Ú…Ò˚ˆπ∆ˆ´')

    dataset = [
        {'pk': 1, 'first_name': u'Brädley', 'last_name': u'∆yers'},
        {'pk': 2, 'first_name': u'Chr…s', 'last_name': u'DÒble'},
    ]

    table = UnicodeTable(dataset)
    request = RequestFactory().get('/some-url/')
    template = Template('{% load django_tables %}{% render_table table %}')
    html = template.render(Context({'request': request, 'table': table}))

    Assert(u'Brädley' in html)
    Assert(u'∆yers' in html)
    Assert(u'Chr…s' in html)
    Assert(u'DÒble' in html)


