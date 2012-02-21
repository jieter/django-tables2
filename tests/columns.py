# -*- coding: utf-8 -*-
"""Test the core table functionality."""
from attest import Tests, Assert
from django_attest import TestContext
import django_tables2 as tables
from django_tables2 import utils, A, Attrs
from django.test.client import RequestFactory
from django.core.urlresolvers import reverse
from django.template import Context, Template
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import ugettext_lazy
from django.utils.translation import ugettext
from itertools import chain
from xml.etree import ElementTree as ET
from .app.models import Person


def attrs(xml):
    """
    Helper function that returns a dict of XML attributes, given an element.
    """
    return ET.fromstring(xml).attrib


checkboxcolumn = Tests()


@checkboxcolumn.test
def attrs_should_be_translated_for_backwards_compatibility():
    class TestTable(tables.Table):
        col = tables.CheckBoxColumn(header_attrs={"th_key": "th_value"},
                                    attrs={"td_key": "td_value"})

    table = TestTable([{"col": "data"}])
    assert attrs(table.columns["col"].header) == {"type": "checkbox", "th_key": "th_value"}
    assert attrs(table.rows[0]["col"])        == {"type": "checkbox", "td_key": "td_value", "value": "data", "name": "col"}


@checkboxcolumn.test
def new_attrs_should_be_supported():
    class TestTable(tables.Table):
        col1 = tables.CheckBoxColumn(attrs=Attrs(th__input={"th_key": "th_value"},
                                                 td__input={"td_key": "td_value"}))
        col2 = tables.CheckBoxColumn(attrs=Attrs(input={"key": "value"}))

    table = TestTable([{"col1": "data", "col2": "data"}])
    assert attrs(table.columns["col1"].header) == {"type": "checkbox", "th_key": "th_value"}
    assert attrs(table.rows[0]["col1"])        == {"type": "checkbox", "td_key": "td_value", "value": "data", "name": "col1"}
    assert attrs(table.columns["col2"].header) == {"type": "checkbox", "key": "value"}
    assert attrs(table.rows[0]["col2"])        == {"type": "checkbox", "key": "value", "value": "data", "name": "col2"}


general = Tests()


@general.test
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


@general.test
def translation():
    """
    Tests different types of values for the ``verbose_name`` property of a
    column.
    """
    class TranslationTable(tables.Table):
        normal = tables.Column(verbose_name=ugettext("Normal"))
        lazy = tables.Column(verbose_name=ugettext("Lazy"))

    table = TranslationTable([])
    Assert("Normal") == table.columns["normal"].header
    Assert("Lazy") == table.columns["lazy"].header


@general.test
def sequence():
    """
    Ensures that the sequence of columns is configurable.
    """
    class TestTable(tables.Table):
        a = tables.Column()
        b = tables.Column()
        c = tables.Column()
    Assert(["a", "b", "c"]) == TestTable([]).columns.names()
    Assert(["b", "a", "c"]) == TestTable([], sequence=("b", "a", "c")).columns.names()

    class TestTable2(TestTable):
        class Meta:
            sequence = ("b", "a", "c")
    Assert(["b", "a", "c"]) == TestTable2([]).columns.names()
    Assert(["a", "b", "c"]) == TestTable2([], sequence=("a", "b", "c")).columns.names()

    # BAD, all columns must be specified, or must use "..."
    with Assert.raises(ValueError):
        class TestTable3(TestTable):
            class Meta:
                sequence = ("a", )
    with Assert.raises(ValueError):
        TestTable([], sequence=("a", ))

    # GOOD, using a single "..." allows you to only specify some columns. The
    # remaining columns are ordered based on their definition order
    class TestTable4(TestTable):
        class Meta:
            sequence = ("...", )
    Assert(["a", "b", "c"]) == TestTable4([]).columns.names()
    Assert(["a", "b", "c"]) == TestTable([], sequence=("...", )).columns.names()

    class TestTable5(TestTable):
        class Meta:
            sequence = ("b", "...")
    Assert(["b", "a", "c"]) == TestTable5([]).columns.names()
    Assert(["b", "a", "c"]) == TestTable([], sequence=("b", "...")).columns.names()

    class TestTable6(TestTable):
        class Meta:
            sequence = ("...", "b")
    Assert(["a", "c", "b"]) == TestTable6([]).columns.names()
    Assert(["a", "c", "b"]) == TestTable([], sequence=("...", "b")).columns.names()

    class TestTable7(TestTable):
        class Meta:
            sequence = ("b", "...", "a")
    Assert(["b", "c", "a"]) == TestTable7([]).columns.names()
    Assert(["b", "c", "a"]) == TestTable([], sequence=("b", "...", "a")).columns.names()

    # Let's test inheritence
    class TestTable8(TestTable):
        d = tables.Column()
        e = tables.Column()
        f = tables.Column()

        class Meta:
            sequence = ("d", "...")

    class TestTable9(TestTable):
        d = tables.Column()
        e = tables.Column()
        f = tables.Column()

    Assert(["d", "a", "b", "c", "e", "f"]) == TestTable8([]).columns.names()
    Assert(["d", "a", "b", "c", "e", "f"]) == TestTable9([], sequence=("d", "...")).columns.names()


@general.test
def should_support_both_meta_sequence_and_constructor_exclude():
    """
    Issue #32 describes a problem when both ``Meta.sequence`` and
    ``Table(..., exclude=...)`` are used on a single table. The bug caused an
    exception to be raised when the table was iterated.
    """
    class SequencedTable(tables.Table):
        a = tables.Column()
        b = tables.Column()
        c = tables.Column()

        class Meta:
            sequence = ('a', '...')

    table = SequencedTable([], exclude=('c', ))
    table.as_html()


@general.test
def bound_columns_should_support_indexing():
    class SimpleTable(tables.Table):
        a = tables.Column()
        b = tables.Column()

    table = SimpleTable([])
    assert 'b' == table.columns[1].name
    assert 'b' == table.columns['b'].name


@general.test
def cell_attrs_applies_to_td_and_th():
    class SimpleTable(tables.Table):
        a = tables.Column(attrs=Attrs(cell={"key": "value"}))

    # providing data ensures 1 row is rendered
    table = SimpleTable([{"a": "value"}])
    root = ET.fromstring(table.as_html())
    assert root.findall('.//thead/tr/th')[0].attrib == {"key": "value", "class": "a"}
    print table.as_html()
    assert root.findall('.//tbody/tr/td')[0].attrib == {"key": "value", "class": "a"}


@general.test
def cells_are_automatically_given_column_name_as_class():
    class SimpleTable(tables.Table):
        a = tables.Column()

    table = SimpleTable([{"a": "value"}])
    root = ET.fromstring(table.as_html())
    assert root.findall('.//thead/tr/th')[0].attrib == {"class": "a"}
    assert root.findall('.//tbody/tr/td')[0].attrib == {"class": "a"}


linkcolumn = Tests()
linkcolumn.context(TestContext())

@linkcolumn.test
def unicode():
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
    template = Template('{% load django_tables2 %}{% render_table table %}')
    html = template.render(Context({'request': request, 'table': table}))

    Assert(u'Brädley' in html)
    Assert(u'∆yers' in html)
    Assert(u'Chr…s' in html)
    Assert(u'DÒble' in html)


@linkcolumn.test
def null_foreign_key():
    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()
        occupation = tables.LinkColumn('occupation', args=[A('occupation.pk')])

    Person.objects.create(first_name='bradley', last_name='ayers')

    table = PersonTable(Person.objects.all())
    table.as_html()


@linkcolumn.test
def kwargs():
    class PersonTable(tables.Table):
        a = tables.LinkColumn('occupation', kwargs={"pk": A('a')})

    html = PersonTable([{"a": 0}, {"a": 1}]).as_html()
    assert reverse("occupation", kwargs={"pk": 0}) in html
    assert reverse("occupation", kwargs={"pk": 1}) in html


@linkcolumn.test
def html_escape_value():
    class PersonTable(tables.Table):
        name = tables.LinkColumn("occupation", kwargs={"pk": A("pk")})

    html = PersonTable([{"name": "<brad>", "pk": 1}]).as_html()
    assert "<brad>" not in html


@linkcolumn.test
def old_style_attrs_should_still_work():
    class TestTable(tables.Table):
        col = tables.LinkColumn('occupation', kwargs={"pk": A('col')},
                                attrs={"title": "Occupation Title"})

    table = TestTable([{"col": 0}])
    assert attrs(table.rows[0]["col"]) == {"href": reverse("occupation", kwargs={"pk": 0}),
                                           "title": "Occupation Title"}


@linkcolumn.test
def a_attrs_should_be_supported():
    class TestTable(tables.Table):
        col = tables.LinkColumn('occupation', kwargs={"pk": A('col')},
                                attrs=Attrs(a={"title": "Occupation Title"}))

    table = TestTable([{"col": 0}])
    assert attrs(table.rows[0]["col"]) == {"href": reverse("occupation", kwargs={"pk": 0}),
                                           "title": "Occupation Title"}


columns = Tests([checkboxcolumn, general, linkcolumn])
