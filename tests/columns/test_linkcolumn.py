# coding: utf-8
from __future__ import unicode_literals

import pytest
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.utils.html import mark_safe

import django_tables2 as tables
from django_tables2 import A

from ..app.models import Occupation, Person
from ..utils import attrs, build_request


def test_unicode():
    """Test LinkColumn"""
    # test unicode values + headings
    class UnicodeTable(tables.Table):
        first_name = tables.LinkColumn('person', args=[A('pk')])
        last_name = tables.LinkColumn('person', args=[A('pk')], verbose_name='äÚ¨´ˆÁ˜¨ˆ˜˘Ú…Ò˚ˆπ∆ˆ´')

    dataset = [
        {'pk': 1, 'first_name': 'Brädley', 'last_name': '∆yers'},
        {'pk': 2, 'first_name': 'Chr…s', 'last_name': 'DÒble'},
    ]

    table = UnicodeTable(dataset)
    request = build_request('/some-url/')
    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': request, 'table': table}))

    assert 'Brädley' in html
    assert '∆yers' in html
    assert 'Chr…s' in html
    assert 'DÒble' in html


def test_link_text_custom_value():
    class CustomLinkTable(tables.Table):
        first_name = tables.LinkColumn('person', text='foo::bar', args=[A('pk')])
        last_name = tables.LinkColumn(
            'person',
            text=lambda row: '%s %s' % (row['last_name'], row['first_name']),
            args=[A('pk')]
        )

    dataset = [
        {'pk': 1, 'first_name': 'John', 'last_name': 'Doe'}
    ]

    table = CustomLinkTable(dataset)
    html = table.as_html(build_request('/some-url/'))

    assert 'foo::bar' in html
    assert 'Doe John' in html


def test_link_text_escaping():
    class CustomLinkTable(tables.Table):
        last_name = tables.LinkColumn(
            'person',
            text=mark_safe('edit'),
            args=[A('pk')]
        )

    dataset = [
        {'pk': 1, 'first_name': 'John', 'last_name': 'Doe'}
    ]

    table = CustomLinkTable(dataset)
    html = table.as_html(build_request('/some-url/'))

    expected = '<td class="last_name"><a href="{}">edit</a></td>'.format(
        reverse('person', args=(1, ))
    )
    assert expected in html


@pytest.mark.django_db
def test_null_foreign_key():
    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()
        occupation = tables.LinkColumn('occupation', args=[A('occupation.pk')])

    Person.objects.create(first_name='bradley', last_name='ayers')

    table = PersonTable(Person.objects.all())
    html = table.as_html(build_request())

    assert '<td class="occupation">—</td>' in html


@pytest.mark.django_db
def test_linkcolumn_non_field_based():
    '''Test for issue 257, non-field based columns'''
    class Table(tables.Table):
        first_name = tables.Column()
        delete_link = tables.LinkColumn('person_delete', text='delete', kwargs={'pk': tables.A('id')})

    willem = Person.objects.create(first_name='Willem', last_name='Wever')

    html = Table(Person.objects.all()).as_html(build_request())

    expected = '<td class="delete_link"><a href="{}">delete</a></td>'.format(
        reverse('person_delete', kwargs={'pk': willem.pk})
    )
    assert expected in html


def test_kwargs():
    class PersonTable(tables.Table):
        a = tables.LinkColumn('occupation', kwargs={'pk': A('a')})

    request = build_request('/')
    html = PersonTable([{'a': 0}, {'a': 1}]).as_html(request)
    assert reverse('occupation', kwargs={'pk': 0}) in html
    assert reverse('occupation', kwargs={'pk': 1}) in html


def test_html_escape_value():
    class PersonTable(tables.Table):
        name = tables.LinkColumn('escaping', kwargs={'pk': A('pk')})

    table = PersonTable([{'name': '<brad>', 'pk': 1}])
    assert table.rows[0].get_cell('name') == '<a href="/&amp;&#39;%22/1/">&lt;brad&gt;</a>'


def test_a_attrs_should_be_supported():
    class TestTable(tables.Table):
        col = tables.LinkColumn('occupation', kwargs={'pk': A('col')},
                                attrs={'a': {'title': 'Occupation Title'}})

    table = TestTable([{'col': 0}])
    assert attrs(table.rows[0].get_cell('col')) == {
        'href': reverse('occupation', kwargs={'pk': 0}),
        'title': 'Occupation Title'
    }


def test_defaults():
    class Table(tables.Table):
        link = tables.LinkColumn('occupation', kwargs={'pk': 1}, default='xyz')

    table = Table([{}])
    assert table.rows[0].get_cell('link') == 'xyz'


@pytest.mark.django_db
def test_get_absolute_url():
    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.LinkColumn()

    person = Person.objects.create(first_name='Jan Pieter', last_name='Waagmeester', )
    table = PersonTable(Person.objects.all())

    expected = '<a href="/people/%d/">Waagmeester</a>' % person.pk
    assert table.rows[0].get_cell('last_name') == expected


def test_get_absolute_url_not_defined():
    class Table(tables.Table):
        first_name = tables.Column()
        last_name = tables.LinkColumn()

    table = Table([
        dict(first_name='Jan Pieter', last_name='Waagmeester')
    ])

    with pytest.raises(TypeError):
        table.as_html(build_request('/'))


@pytest.mark.django_db
def test_RelatedLinkColumn():
    carpenter = Occupation.objects.create(name='Carpenter')
    Person.objects.create(first_name='Bob', last_name='Builder', occupation=carpenter)

    class Table(tables.Table):
        first_name = tables.LinkColumn()
        last_name = tables.Column()
        occupation = tables.RelatedLinkColumn()

    table = Table(Person.objects.all())

    assert table.rows[0].get_cell('occupation') == '<a href="/occupations/%d/">Carpenter</a>' % carpenter.pk
