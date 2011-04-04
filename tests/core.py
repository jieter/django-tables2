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
def sorting(context):
    class MyUnsortedTable(tables.Table):
        i = tables.Column()
        alpha = tables.Column()
        beta = tables.Column()

    # various different ways to say the same thing: don't sort
    Assert(MyUnsortedTable([]).order_by) == ()
    Assert(MyUnsortedTable([], order_by=None).order_by) == ()
    Assert(MyUnsortedTable([], order_by=[]).order_by) == ()
    Assert(MyUnsortedTable([], order_by=()).order_by) == ()

    # values of order_by are wrapped in tuples before being returned
    Assert(MyUnsortedTable([], order_by='alpha').order_by) == ('alpha',)
    Assert(MyUnsortedTable([], order_by=('beta',)).order_by) == ('beta',)

    # a rewritten order_by is also wrapped
    table = MyUnsortedTable([])
    table.order_by = 'alpha'
    assert ('alpha', ) == table.order_by

    # default sort order can be specified in table options
    class MySortedTable(MyUnsortedTable):
        class Meta:
            order_by = 'alpha'

    # order_by is inherited from the options if not explitly set
    table = MySortedTable([])
    assert ('alpha',) == table.order_by

    # ...but can be overloaded at __init___
    table = MySortedTable([], order_by='beta')
    assert ('beta',) == table.order_by

    # ...or rewritten later
    table = MySortedTable(context.memory_data)
    table.order_by = 'beta'
    assert ('beta',) == table.order_by
    assert 3 == table.rows[0]['i']

    # ...or reset to None (unsorted), ignoring the table default
    table = MySortedTable(context.memory_data, order_by=None)
    assert () == table.order_by
    assert 2 == table.rows[0]['i']


@core.test
def row_subscripting(context):
    row = context.table.rows[0]
    # attempt number indexing
    Assert(row[0]) == 2
    Assert(row[1]) == 'b'
    Assert(row[2]) == 'b'
    with Assert.raises(IndexError) as error:
        row[3]
    # attempt column name indexing
    Assert(row['i']) == 2
    Assert(row['alpha']) == 'b'
    Assert(row['beta']) == 'b'
    with Assert.raises(KeyError) as error:
        row['gamma']


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
    Assert(row['col1']) == True
    Assert(row['col2']) == 'B'


@core.test
def pagination():
    class BookTable(tables.Table):
        name = tables.Column()

    # create some sample data
    data = []
    for i in range(1,101):
        data.append({'name': 'Book Nr. %d' % i})
    books = BookTable(data)

    # external paginator
    paginator = Paginator(books.rows, 10)
    assert paginator.num_pages == 10
    page = paginator.page(1)
    assert page.has_previous() == False
    assert page.has_next() == True

    # integrated paginator
    books.paginate(Paginator, page=1, per_page=10)
    # rows is now paginated
    assert len(list(books.rows.page())) == 10
    assert len(list(books.rows.all())) == 100
    # new attributes
    assert books.paginator.num_pages == 10
    assert books.page.has_previous() == False
    assert books.page.has_next() == True
    # exceptions are converted into 404s
    with Assert.raises(Http404) as error:
        books.paginate(Paginator, page=9999, per_page=10)
        books.paginate(Paginator, page='abc', per_page=10)


if __name__ == '__main__':
    core.main()
