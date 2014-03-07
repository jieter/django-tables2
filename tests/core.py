# coding: utf-8
"""Test the core table functionality."""
from __future__ import absolute_import, unicode_literals
from attest import assert_hook, raises, Tests, warns
import copy
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
import django_tables2 as tables
from django_tables2.tables import DeclarativeColumnsMetaclass
import six
import itertools


core = Tests()


class UnorderedTable(tables.Table):
    i = tables.Column()
    alpha = tables.Column()
    beta = tables.Column()


class OrderedTable(UnorderedTable):
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
def metaclass_inheritance():
    class Tweaker(type):
        """Adds an attribute "tweaked" to all classes"""
        def __new__(cls, name, bases, attrs):
            attrs['tweaked'] = True
            return super(Tweaker, cls).__new__(cls, name, bases, attrs)

    class Meta(Tweaker, DeclarativeColumnsMetaclass):
        pass

    class TweakedTableBase(tables.Table):
        __metaclass__ = Meta
        name = tables.Column()

    # Python 2/3 compatible way to enable the metaclass
    TweakedTable = Meta(str('TweakedTable'), (TweakedTableBase, ), {})

    table = TweakedTable([])
    assert 'name' in table.columns
    assert table.tweaked

    # now flip the order
    class FlippedMeta(DeclarativeColumnsMetaclass, Tweaker):
        pass

    class FlippedTweakedTableBase(tables.Table):
        name = tables.Column()

    # Python 2/3 compatible way to enable the metaclass
    FlippedTweakedTable = FlippedMeta(str('FlippedTweakedTable'), (FlippedTweakedTableBase, ), {})

    table = FlippedTweakedTable([])
    assert 'name' in table.columns
    assert table.tweaked


@core.test
def attrs():
    class TestTable(tables.Table):
        class Meta:
            attrs = {}
    assert {} == TestTable([]).attrs

    class TestTable2(tables.Table):
        class Meta:
            attrs = {"a": "b"}
    assert {"a": "b"} == TestTable2([]).attrs

    class TestTable3(tables.Table):
        pass
    assert {} == TestTable3([]).attrs
    assert {"a": "b"} == TestTable3([], attrs={"a": "b"}).attrs

    class TestTable4(tables.Table):
        class Meta:
            attrs = {"a": "b"}
    assert {"c": "d"} == TestTable4([], attrs={"c": "d"}).attrs


@core.test
def attrs_support_computed_values():
    counter = itertools.count()

    class TestTable(tables.Table):
        class Meta:
            attrs = {"id": lambda: "test_table_%d" % next(counter)}

    assert {"id": "test_table_0"} == TestTable([]).attrs
    assert {"id": "test_table_1"} == TestTable([]).attrs


@core.test
def data_knows_its_name():
    table = tables.Table([{}])
    assert table.data.verbose_name == "item"
    assert table.data.verbose_name_plural == "items"


@core.test
def datasource_untouched():
    """Ensure that data that is provided to the table (the datasource) is not
    modified by table operations.
    """
    original_data = copy.deepcopy(MEMORY_DATA)

    table = UnorderedTable(MEMORY_DATA)
    table.order_by = 'i'
    list(table.rows)
    assert MEMORY_DATA == original_data

    table = UnorderedTable(MEMORY_DATA)
    table.order_by = 'beta'
    list(table.rows)
    assert MEMORY_DATA == original_data


@core.test
def should_support_tuple_data_source():
    class SimpleTable(tables.Table):
        name = tables.Column()

    table = SimpleTable((
        {'name': 'brad'},
        {'name': 'stevie'},
    ))

    assert len(table.rows) == 2


@core.test_if(not six.PY3)  # Haystack isn't compatible with Python 3
def should_support_haystack_data_source():
    from haystack.query import SearchQuerySet

    class PersonTable(tables.Table):
        first_name = tables.Column()

    table = PersonTable(SearchQuerySet().all())
    table.as_html()


@core.test
def data_validation():
    with raises(ValueError):
        table = OrderedTable(None)
    
    class Bad:
        def __len__(self):
            pass
      
    with raises(ValueError):
        table = OrderedTable(Bad())

    class Ok:
        def __len__(self):
            return 1
        def __getitem__(self, pos):
            if pos != 0:
                raise IndexError()
            return {'a': 1}
    
    table = OrderedTable(Ok())
    assert len(table.rows) == 1

@core.test
def ordering():
    # fallback to Table.Meta
    assert ('alpha', ) == OrderedTable([], order_by=None).order_by == OrderedTable([]).order_by

    # values of order_by are wrapped in tuples before being returned
    assert OrderedTable([], order_by='alpha').order_by   == ('alpha', )
    assert OrderedTable([], order_by=('beta',)).order_by == ('beta', )

    table = OrderedTable([])
    table.order_by = []
    assert () == table.order_by == OrderedTable([], order_by=[]).order_by

    table = OrderedTable([])
    table.order_by = ()
    assert () == table.order_by == OrderedTable([], order_by=()).order_by

    table = OrderedTable([])
    table.order_by = ''
    assert () == table.order_by == OrderedTable([], order_by='').order_by

    # apply an ordering
    table = UnorderedTable([])
    table.order_by = 'alpha'
    assert ('alpha', ) == UnorderedTable([], order_by='alpha').order_by == table.order_by

    table = OrderedTable([])
    table.order_by = 'alpha'
    assert ('alpha', ) == OrderedTable([], order_by='alpha').order_by  == table.order_by

    # let's check the data
    table = OrderedTable(MEMORY_DATA, order_by='beta')
    assert 3 == table.rows[0]['i']

    table = OrderedTable(MEMORY_DATA, order_by='-beta')
    assert 1 == table.rows[0]['i']

    # allow fallback to Table.Meta.order_by
    table = OrderedTable(MEMORY_DATA)
    assert 1 == table.rows[0]['i']

    # column's can't be ordered if they're not allowed to be
    class TestTable2(tables.Table):
        a = tables.Column(orderable=False)
        b = tables.Column()

    table = TestTable2([], order_by='a')
    assert table.order_by == ()

    table = TestTable2([], order_by='b')
    assert table.order_by == ('b', )

    # ordering disabled by default
    class TestTable3(tables.Table):
        a = tables.Column(orderable=True)
        b = tables.Column()

        class Meta:
            orderable = False

    table = TestTable3([], order_by='a')
    assert table.order_by == ('a', )

    table = TestTable3([], order_by='b')
    assert table.order_by == ()

    table = TestTable3([], orderable=True, order_by='b')
    assert table.order_by == ('b', )

    with warns(DeprecationWarning) as captured:
        tables.Column(sortable=True)
        tables.Column(sortable=False)

        class TestTable4(tables.Table):
            class Meta:
                sortable = True

        class TestTable4(tables.Table):
            class Meta:
                sortable = False

    assert len(captured) == 4


@core.test
def ordering_different_types():
    from datetime import datetime

    data = [
        {'i': 1, 'alpha': datetime.now(), 'beta': [1]},
        {'i': {}, 'alpha': None, 'beta': ''},
        {'i': 2, 'alpha': None, 'beta': []},
    ]

    table = OrderedTable(data)
    assert "—" == table.rows[0]['alpha']

    table = OrderedTable(data, order_by='i')
    if six.PY3:
        assert {} == table.rows[0]['i']
    else:
        assert 1 == table.rows[0]['i']


    table = OrderedTable(data, order_by='beta')
    assert [] == table.rows[0]['beta']


@core.test
def multi_column_ordering():
    brad   = {"first_name": "Bradley", "last_name": "Ayers"}
    brad2  = {"first_name": "Bradley", "last_name": "Fake"}
    chris  = {"first_name": "Chris",   "last_name": "Doble"}
    stevie = {"first_name": "Stevie",  "last_name": "Armstrong"}
    ross   = {"first_name": "Ross",    "last_name": "Ayers"}

    people = [brad, brad2, chris, stevie, ross]

    class PersonTable(tables.Table):
        first_name = tables.Column()
        last_name = tables.Column()

    table = PersonTable(people, order_by=("first_name", "last_name"))
    assert [brad, brad2, chris, ross, stevie] == [r.record for r in table.rows]

    table = PersonTable(people, order_by=("first_name", "-last_name"))
    assert [brad2, brad, chris, ross, stevie] == [r.record for r in table.rows]

    # let's try column order_by using multiple keys
    class PersonTable(tables.Table):
        name = tables.Column(order_by=("first_name", "last_name"))

    # add 'name' key for each person.
    for person in people:
        person['name'] = "{p[first_name]} {p[last_name]}".format(p=person)
    assert brad['name'] == "Bradley Ayers"

    table = PersonTable(people, order_by="name")
    assert [brad, brad2, chris, ross, stevie] == [r.record for r in table.rows]

    table = PersonTable(people, order_by="-name")
    assert [stevie, ross, chris, brad2, brad] == [r.record for r in table.rows]


@core.test
def column_count():
    class SimpleTable(tables.Table):
        visible = tables.Column(visible=True)
        hidden = tables.Column(visible=False)

    # The columns container supports the len() builtin
    assert len(SimpleTable([]).columns) == 1


@core.test
def column_accessor():
    class SimpleTable(UnorderedTable):
        col1 = tables.Column(accessor='alpha.upper.isupper')
        col2 = tables.Column(accessor='alpha.upper')
    table = SimpleTable(MEMORY_DATA)
    row = table.rows[0]
    assert row['col1'] is True
    assert row['col2'] == 'B'


@core.test
def exclude_columns():
    """
    Defining ``Table.Meta.exclude`` or providing an ``exclude`` argument when
    instantiating a table should have the same effect -- exclude those columns
    from the table. It should have the same effect as not defining the
    columns originally.
    """
    # Table(..., exclude=...)
    table = UnorderedTable([], exclude=("i"))
    assert [c.name for c in table.columns] == ["alpha", "beta"]

    # Table.Meta: exclude=...
    class PartialTable(UnorderedTable):
        class Meta:
            exclude = ("alpha", )
    table = PartialTable([])
    assert [c.name for c in table.columns] == ["i", "beta"]

    # Inheritence -- exclude in parent, add in child
    class AddonTable(PartialTable):
        added = tables.Column()
    table = AddonTable([])
    assert [c.name for c in table.columns] == ["i", "beta", "added"]

    # Inheritence -- exclude in child
    class ExcludeTable(UnorderedTable):
        added = tables.Column()
        class Meta:
            exclude = ("beta", )
    table = ExcludeTable([])
    assert [c.name for c in table.columns] == ["i", "alpha", "added"]


@core.test
def table_exclude_property_should_override_constructor_argument():
    class SimpleTable(tables.Table):
        a = tables.Column()
        b = tables.Column()

    table = SimpleTable([], exclude=('b', ))
    assert [c.name for c in table.columns] == ['a']
    table.exclude = ('a', )
    assert [c.name for c in table.columns] == ['b']


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
    assert hasattr(books, "page") is True

    books.paginate(page=1, per_page=10)
    assert len(list(books.page.object_list)) == 10

    # new attributes
    assert books.paginator.num_pages == 10
    assert books.page.has_previous() is False
    assert books.page.has_next() is True

    # accessing a non-existant page raises 404
    with raises(EmptyPage):
        books.paginate(Paginator, page=9999, per_page=10)

    with raises(PageNotAnInteger):
        books.paginate(Paginator, page='abc', per_page=10)


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
    assert table.empty_text is None

    class TestTable2(tables.Table):
        a = tables.Column()

        class Meta:
            empty_text = 'nothing here'

    table = TestTable2([])
    assert table.empty_text == 'nothing here'

    table = TestTable2([], empty_text='still nothing')
    assert table.empty_text == 'still nothing'


@core.test
def prefix():
    """Test that table prefixes affect the names of querystring parameters"""
    class TableA(tables.Table):
        name = tables.Column()

        class Meta:
            prefix = "x"

    assert "x" == TableA([]).prefix

    class TableB(tables.Table):
        name = tables.Column()

    assert "" == TableB([]).prefix
    assert "x" == TableB([], prefix="x").prefix

    table = TableB([])
    table.prefix = "x"
    assert "x" == table.prefix


@core.test
def field_names():
    class TableA(tables.Table):
        class Meta:
            order_by_field = "abc"
            page_field = "def"
            per_page_field = "ghi"

    table = TableA([])
    assert "abc" == table.order_by_field
    assert "def" == table.page_field
    assert "ghi" == table.per_page_field


@core.test
def field_names_with_prefix():
    class TableA(tables.Table):
        class Meta:
            order_by_field = "sort"
            page_field = "page"
            per_page_field = "per_page"
            prefix = "1-"

    table = TableA([])
    assert "1-sort" == table.prefixed_order_by_field
    assert "1-page" == table.prefixed_page_field
    assert "1-per_page" == table.prefixed_per_page_field

    class TableB(tables.Table):
        class Meta:
            order_by_field = "sort"
            page_field = "page"
            per_page_field = "per_page"

    table = TableB([], prefix="1-")
    assert "1-sort" == table.prefixed_order_by_field
    assert "1-page" == table.prefixed_page_field
    assert "1-per_page" == table.prefixed_per_page_field

    table = TableB([])
    table.prefix = "1-"
    assert "1-sort" == table.prefixed_order_by_field
    assert "1-page" == table.prefixed_page_field
    assert "1-per_page" == table.prefixed_per_page_field


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


@core.test
def column_defaults_are_honored():
    class Table(tables.Table):
        name = tables.Column(default="abcd")

        class Meta:
            default = "efgh"

    table = Table([{}], default="ijkl")
    assert table.rows[0]['name'] == "abcd"


@core.test
def table_meta_defaults_are_honored():
    class Table(tables.Table):
        name = tables.Column()

        class Meta:
            default = "abcd"

    table = Table([{}])
    assert table.rows[0]['name'] == "abcd"


@core.test
def table_defaults_are_honored():
    class Table(tables.Table):
        name = tables.Column()

    table = Table([{}], default="abcd")
    assert table.rows[0]['name'] == "abcd"

    table = Table([{}], default="abcd")
    table.default = "efgh"
    assert table.rows[0]['name'] == "efgh"


@core.test
def list_table_data_supports_ordering():
    class Table(tables.Table):
        name = tables.Column()

    data = [
        {"name": "Bradley"},
        {"name": "Stevie"},
    ]

    table = Table(data)
    assert table.rows[0]["name"] == "Bradley"
    table.order_by = "-name"
    assert table.rows[0]["name"] == "Stevie"
