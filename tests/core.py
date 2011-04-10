"""Test the core table functionality."""
import copy
from attest import Tests, Assert
from django.http import Http404
from django.core.paginator import Paginator
import django_tables as tables
from django_tables import utils

core = Tests()


@core.context
def context():
    class Context(object):
        memory_data = [
            {'i': 2, 'alpha': 'b', 'beta': 'b'},
            {'i': 1, 'alpha': 'a', 'beta': 'c'},
            {'i': 3, 'alpha': 'c', 'beta': 'a'},
        ]

        class UnsortedTable(tables.Table):
            i = tables.Column()
            alpha = tables.Column()
            beta = tables.Column()

        class SortedTable(UnsortedTable):
            class Meta:
                order_by = 'alpha'

        table = UnsortedTable(memory_data)

    yield Context


@core.test
def declarations(context):
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
def datasource_untouched(context):
    """Ensure that data that is provided to the table (the datasource) is not
    modified by table operations.
    """
    original_data = copy.deepcopy(context.memory_data)

    table = context.UnsortedTable(context.memory_data)
    table.order_by = 'i'
    list(table.rows)
    assert context.memory_data == Assert(original_data)

    table = context.UnsortedTable(context.memory_data)
    table.order_by = 'beta'
    list(table.rows)
    assert context.memory_data == Assert(original_data)


@core.test
def sorting(ctx):
    # fallback to Table.Meta
    Assert(('alpha', )) == ctx.SortedTable([], order_by=None).order_by == ctx.SortedTable([]).order_by

    # values of order_by are wrapped in tuples before being returned
    Assert(ctx.SortedTable([], order_by='alpha').order_by)   == ('alpha', )
    Assert(ctx.SortedTable([], order_by=('beta',)).order_by) == ('beta', )

    # "no sorting"
    table = ctx.SortedTable([])
    table.order_by = []
    Assert(()) == table.order_by == ctx.SortedTable([], order_by=[]).order_by

    table = ctx.SortedTable([])
    table.order_by = ()
    Assert(()) == table.order_by == ctx.SortedTable([], order_by=()).order_by

    table = ctx.SortedTable([])
    table.order_by = ''
    Assert(()) == table.order_by == ctx.SortedTable([], order_by='').order_by

    # apply a sorting
    table = ctx.UnsortedTable([])
    table.order_by = 'alpha'
    Assert(('alpha', )) == ctx.UnsortedTable([], order_by='alpha').order_by == table.order_by

    table = ctx.SortedTable([])
    table.order_by = 'alpha'
    Assert(('alpha', )) == ctx.SortedTable([], order_by='alpha').order_by  == table.order_by

    # let's check the data
    table = ctx.SortedTable(ctx.memory_data, order_by='beta')
    Assert(3) == table.rows[0]['i']

    # allow fallback to Table.Meta.order_by
    table = ctx.SortedTable(ctx.memory_data)
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
def column_count(context):
    class SimpleTable(tables.Table):
        visible = tables.Column(visible=True)
        hidden = tables.Column(visible=False)

    # The columns container supports the len() builtin
    assert len(SimpleTable([]).columns) == 1


@core.test
def column_accessor(context):
    class SimpleTable(context.UnsortedTable):
        col1 = tables.Column(accessor='alpha.upper.isupper')
        col2 = tables.Column(accessor='alpha.upper')
    table = SimpleTable(context.memory_data)
    row = table.rows[0]
    Assert(row['col1']) is True
    Assert(row['col2']) == 'B'


@core.test
def pagination():
    class BookTable(tables.Table):
        name = tables.Column()

    # create some sample data
    data = []
    for i in range(100):
        data.append({'name': 'Book No. %d' % i})
    books = BookTable(data)

    # external paginator
    paginator = Paginator(books.rows, 10)
    assert paginator.num_pages == 10
    page = paginator.page(1)
    assert page.has_previous() is False
    assert page.has_next() is True

    # integrated paginator
    books.paginate(page=1)
    Assert(hasattr(books, 'page')) is True

    books.paginate(page=1, per_page=10)
    Assert(len(list(books.page.object_list))) == 10

    # new attributes
    Assert(books.paginator.num_pages) == 10
    Assert(books.page.has_previous()) is False
    Assert(books.page.has_next()) is True

    # exceptions are converted into 404s
    with Assert.raises(Http404) as error:
        books.paginate(Paginator, page=9999, per_page=10)
        books.paginate(Paginator, page='abc', per_page=10)


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
