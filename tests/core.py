# -*- coding: utf-8 -*-
"""Test the core table functionality."""
from __future__ import absolute_import
from attest import Tests, Assert
import copy
from django.http import Http404
from django.core.paginator import Paginator
import django_tables2 as tables
from django_tables2 import utils
from haystack.query import SearchQuerySet


core = Tests()


class UnsortedTable(tables.Table):
    i = tables.Column()
    alpha = tables.Column()
    beta = tables.Column()


class SortedTable(UnsortedTable):
    class Meta:
        order_by = 'alpha'


MEMORY_DATA = [
    {'i': 2, 'alpha': 'b', 'beta': 'b'},
    {'i': 1, 'alpha': 'a', 'beta': 'c'},
    {'i': 3, 'alpha': 'c', 'beta': 'a'},
]


@core.test
def declarations():
    """Test defining tables by declaration."""
    class GeoAreaTable(tables.Table):
        name = tables.Column()
        population = tables.Column()

    assert len(GeoAreaTable.base_columns) == 2
    assert 'name' in GeoAreaTable.base_columns
    assert not hasattr(GeoAreaTable, 'name')

    class CountryTable(GeoAreaTable):
        capital = tables.Column()

    assert len(CountryTable.base_columns) == 3
    assert 'capital' in CountryTable.base_columns

    # multiple inheritance
    class AddedMixin(tables.Table):
        added = tables.Column()

    class CityTable(GeoAreaTable, AddedMixin):
        mayor = tables.Column()

    assert len(CityTable.base_columns) == 4
    assert 'added' in CityTable.base_columns


@core.test
def attrs():
    class TestTable(tables.Table):
        class Meta:
            attrs = {}
    Assert({}) == TestTable([]).attrs

    class TestTable2(tables.Table):
        class Meta:
            attrs = {"a": "b"}
    Assert({"a": "b"}) == TestTable2([]).attrs

    class TestTable3(tables.Table):
        pass
    Assert({}) == TestTable3([]).attrs
    Assert({"a": "b"}) == TestTable3([], attrs={"a": "b"}).attrs

    class TestTable4(tables.Table):
        class Meta:
            attrs = {"a": "b"}
    Assert({"c": "d"}) == TestTable4([], attrs={"c": "d"}).attrs


@core.test
def datasource_untouched():
    """Ensure that data that is provided to the table (the datasource) is not
    modified by table operations.
    """
    original_data = copy.deepcopy(MEMORY_DATA)

    table = UnsortedTable(MEMORY_DATA)
    table.order_by = 'i'
    list(table.rows)
    assert MEMORY_DATA == Assert(original_data)

    table = UnsortedTable(MEMORY_DATA)
    table.order_by = 'beta'
    list(table.rows)
    assert MEMORY_DATA == Assert(original_data)


@core.test
def should_support_tuple_data_source():
    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable((
        {'name': 'brad'},
        {'name': 'stevie'},
    ))

    assert len(table.rows) == 2

@core.test
def should_support_haystack_data_source():
    class PersonTable(tables.Table):
        first_name = tables.Column()

    table = PersonTable(SearchQuerySet().all())
    table.as_html()


@core.test
def sorting():
    # fallback to Table.Meta
    Assert(('alpha', )) == SortedTable([], order_by=None).order_by == SortedTable([]).order_by

    # values of order_by are wrapped in tuples before being returned
    Assert(SortedTable([], order_by='alpha').order_by)   == ('alpha', )
    Assert(SortedTable([], order_by=('beta',)).order_by) == ('beta', )

    # "no sorting"
    table = SortedTable([])
    table.order_by = []
    Assert(()) == table.order_by == SortedTable([], order_by=[]).order_by

    table = SortedTable([])
    table.order_by = ()
    Assert(()) == table.order_by == SortedTable([], order_by=()).order_by

    table = SortedTable([])
    table.order_by = ''
    Assert(()) == table.order_by == SortedTable([], order_by='').order_by

    # apply a sorting
    table = UnsortedTable([])
    table.order_by = 'alpha'
    Assert(('alpha', )) == UnsortedTable([], order_by='alpha').order_by == table.order_by

    table = SortedTable([])
    table.order_by = 'alpha'
    Assert(('alpha', )) == SortedTable([], order_by='alpha').order_by  == table.order_by

    # let's check the data
    table = SortedTable(MEMORY_DATA, order_by='beta')
    Assert(3) == table.rows[0]['i']

    # allow fallback to Table.Meta.order_by
    table = SortedTable(MEMORY_DATA)
    Assert(1) == table.rows[0]['i']

    # column's can't be sorted if they're not allowed to be
    class TestTable(tables.Table):
        a = tables.Column(sortable=False)
        b = tables.Column()

    table = TestTable([], order_by='a')
    Assert(table.order_by) == ()

    table = TestTable([], order_by='b')
    Assert(table.order_by) == ('b', )

    # sorting disabled by default
    class TestTable(tables.Table):
        a = tables.Column(sortable=True)
        b = tables.Column()

        class Meta:
            sortable = False

    table = TestTable([], order_by='a')
    Assert(table.order_by) == ('a', )

    table = TestTable([], order_by='b')
    Assert(table.order_by) == ()

    table = TestTable([], sortable=True, order_by='b')
    Assert(table.order_by) == ('b', )


@core.test
def sorting_different_types():
    from datetime import datetime

    data = [
        {'i': 1, 'alpha': datetime.now(), 'beta': [1]},
        {'i': {}, 'alpha': None, 'beta': ''},
        {'i': 2, 'alpha': None, 'beta': []},
    ]

    table = SortedTable(data)
    Assert(None) == table.rows[0]['alpha']

    table = SortedTable(data, order_by='i')
    Assert(1) == table.rows[0]['i']

    table = SortedTable(data, order_by='beta')
    Assert([]) == table.rows[0]['beta']


@core.test
def column_count():
    class SimpleTable(tables.Table):
        visible = tables.Column(visible=True)
        hidden = tables.Column(visible=False)

    # The columns container supports the len() builtin
    assert len(SimpleTable([]).columns) == 1


@core.test
def column_accessor():
    class SimpleTable(UnsortedTable):
        col1 = tables.Column(accessor='alpha.upper.isupper')
        col2 = tables.Column(accessor='alpha.upper')
    table = SimpleTable(MEMORY_DATA)
    row = table.rows[0]
    Assert(row['col1']) is True
    Assert(row['col2']) == 'B'


@core.test
def exclude_columns():
    """
    Defining ``Table.Meta.exclude`` or providing an ``exclude`` argument when
    instantiating a table should have the same effect -- exclude those columns
    from the table. It should have the same effect as not defining the
    columns originally.
    """
    # Table(..., exclude=...)
    table = UnsortedTable([], exclude=("i"))
    Assert([c.name for c in table.columns]) == ["alpha", "beta"]

    # Table.Meta: exclude=...
    class PartialTable(UnsortedTable):
        class Meta:
            exclude = ("alpha", )
    table = PartialTable([])
    Assert([c.name for c in table.columns]) == ["i", "beta"]

    # Inheritence -- exclude in parent, add in child
    class AddonTable(PartialTable):
        added = tables.Column()
    table = AddonTable([])
    Assert([c.name for c in table.columns]) == ["i", "beta", "added"]

    # Inheritence -- exclude in child
    class ExcludeTable(UnsortedTable):
        added = tables.Column()
        class Meta:
            exclude = ("beta", )
    table = ExcludeTable([])
    Assert([c.name for c in table.columns]) == ["i", "alpha", "added"]


@core.test
def table_exclude_property_should_override_constructor_argument():
    class SimpleTable(tables.Table):
        a = tables.Column()
        b = tables.Column()

    table = SimpleTable([], exclude=('b', ))
    Assert([c.name for c in table.columns]) == ['a']
    table.exclude = ('a', )
    Assert([c.name for c in table.columns]) == ['b']



@core.test
def pagination():
    class BookTable(tables.Table):
        name = tables.Column()

    # create some sample data
    data = []
    for i in range(100):
        data.append({"name": "Book No. %d" % i})
    books = BookTable(data)

    # external paginator
    paginator = Paginator(books.rows, 10)
    assert paginator.num_pages == 10
    page = paginator.page(1)
    assert page.has_previous() is False
    assert page.has_next() is True

    # integrated paginator
    books.paginate(page=1)
    Assert(hasattr(books, "page")) is True

    books.paginate(page=1, per_page=10)
    Assert(len(list(books.page.object_list))) == 10

    # new attributes
    Assert(books.paginator.num_pages) == 10
    Assert(books.page.has_previous()) is False
    Assert(books.page.has_next()) is True

    # accessing a non-existant page raises 404
    with Assert.raises(Http404) as error:
        books.paginate(Paginator, page=9999, per_page=10)
        books.page

    with Assert.raises(Http404) as error:
        books.paginate(Paginator, page='abc', per_page=10)
        books.page

@core.test
def pagination_shouldnt_prevent_multiple_rendering():
    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable([{'name': 'brad'}])
    table.paginate()

    assert table.as_html() == table.as_html()


@core.test
def empty_text():
    class TestTable(tables.Table):
        a = tables.Column()

    table = TestTable([])
    Assert(table.empty_text) is None

    class TestTable(tables.Table):
        a = tables.Column()

        class Meta:
            empty_text = 'nothing here'

    table = TestTable([])
    Assert(table.empty_text) == 'nothing here'

    table = TestTable([], empty_text='still nothing')
    Assert(table.empty_text) == 'still nothing'


@core.test
def prefix():
    """Test that table prefixes affect the names of querystring parameters"""
    class TableA(tables.Table):
        name = tables.Column()

        class Meta:
            prefix = "x"

    Assert("x") == TableA([]).prefix

    class TableB(tables.Table):
        name = tables.Column()

    Assert("") == TableB([]).prefix
    Assert("x") == TableB([], prefix="x").prefix

    table = TableB([])
    table.prefix = "x"
    Assert("x") == table.prefix


@core.test
def field_names():
    class TableA(tables.Table):
        class Meta:
            order_by_field = "abc"
            page_field = "def"
            per_page_field = "ghi"

    table = TableA([])
    Assert("abc") == table.order_by_field
    Assert("def") == table.page_field
    Assert("ghi") == table.per_page_field


@core.test
def field_names_with_prefix():
    class TableA(tables.Table):
        class Meta:
            order_by_field = "sort"
            page_field = "page"
            per_page_field = "per_page"
            prefix = "1-"

    table = TableA([])
    Assert("1-sort") == table.prefixed_order_by_field
    Assert("1-page") == table.prefixed_page_field
    Assert("1-per_page") == table.prefixed_per_page_field

    class TableB(tables.Table):
        class Meta:
            order_by_field = "sort"
            page_field = "page"
            per_page_field = "per_page"

    table = TableB([], prefix="1-")
    Assert("1-sort") == table.prefixed_order_by_field
    Assert("1-page") == table.prefixed_page_field
    Assert("1-per_page") == table.prefixed_per_page_field

    table = TableB([])
    table.prefix = "1-"
    Assert("1-sort") == table.prefixed_order_by_field
    Assert("1-page") == table.prefixed_page_field
    Assert("1-per_page") == table.prefixed_per_page_field


@core.test
def should_support_a_template_to_be_specified():
    class MetaDeclarationSpecifiedTemplateTable(tables.Table):
        name = tables.Column()

        class Meta:
            template = "dummy.html"

    table = MetaDeclarationSpecifiedTemplateTable([])
    assert table.template == "dummy.html"

    class ConstructorSpecifiedTemplateTable(tables.Table):
        name = tables.Column()

    table = ConstructorSpecifiedTemplateTable([], template="dummy.html")
    assert table.template == "dummy.html"

    class PropertySpecifiedTemplateTable(tables.Table):
        name = tables.Column()

    table = PropertySpecifiedTemplateTable([])
    table.template = "dummy.html"
    assert table.template == "dummy.html"

    class DefaultTable(tables.Table):
        pass

    table = DefaultTable([])
    assert table.template == "django_tables2/table.html"


@core.test
def should_support_rendering_multiple_times():
    class MultiRenderTable(tables.Table):
        name = tables.Column()

    # test list data
    table = MultiRenderTable([{'name': 'brad'}])
    assert table.as_html() == table.as_html()
