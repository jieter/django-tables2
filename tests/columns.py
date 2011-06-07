# -*- coding: utf-8 -*-
"""Test the core table functionality."""
from attest import Tests, Assert
from django_attest import TransactionTestContext
from django.test.client import RequestFactory
from django.template import Context, Template
from django.core.exceptions import ImproperlyConfigured
import django_tables as tables
from django_tables import utils, A
from .testapp.models import Person


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


linkcolumn = Tests()
linkcolumn.context(TransactionTestContext())

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
    template = Template('{% load django_tables %}{% render_table table %}')
    html = template.render(Context({'request': request, 'table': table}))

    Assert(u'Brädley' in html)
    Assert(u'∆yers' in html)
    Assert(u'Chr…s' in html)
    Assert(u'DÒble' in html)

    # Test handling queryset data with a null foreign key


@linkcolumn.test
def null_foreign_key():
    """

    """
    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()
        occupation = tables.LinkColumn('occupation', args=[A('occupation.pk')])

    Person.objects.create(first_name='bradley', last_name='ayers')

    table = PersonTable(Person.objects.all())
    table.as_html()


columns = Tests([general, linkcolumn])
