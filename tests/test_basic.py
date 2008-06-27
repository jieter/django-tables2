"""Test the base table functionality.

This includes the core, as well as static data, non-model tables.
"""

from math import sqrt
from py.test import raises
from django.core.paginator import Paginator
import django_tables as tables

def test_declaration():
    """
    Test defining tables by declaration.
    """

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
        mayer = tables.Column()

    assert len(CityTable.base_columns) == 4
    assert 'added' in CityTable.base_columns

    # modelforms: support switching from a non-model table hierarchy to a
    # modeltable hierarchy (both base class orders)
    class StateTable1(tables.ModelTable, GeoAreaTable):
        motto = tables.Column()
    class StateTable2(GeoAreaTable, tables.ModelTable):
        motto = tables.Column()

    assert len(StateTable1.base_columns) == len(StateTable2.base_columns) == 3
    assert 'motto' in StateTable1.base_columns
    assert 'motto' in StateTable2.base_columns

def test_basic():
    class StuffTable(tables.Table):
        name = tables.Column()
        answer = tables.Column(default=42)
        c = tables.Column(name="count", default=1)
        email = tables.Column(data="@")
    stuff = StuffTable([
        {'id': 1, 'name': 'Foo Bar', '@': 'foo@bar.org'},
    ])

    # access without order_by works
    stuff.data
    stuff.rows

    # make sure BoundColumnn.name always gives us the right thing, whether
    # the column explicitely defines a name or not.
    stuff.columns['count'].name == 'count'
    stuff.columns['answer'].name == 'answer'

    for r in stuff.rows:
        # unknown fields are removed/not-accessible
        assert 'name' in r
        assert not 'id' in r
        # missing data is available as default
        assert 'answer' in r
        assert r['answer'] == 42   # note: different from prev. line!

        # all that still works when name overrides are used
        assert not 'c' in r
        assert 'count' in r
        assert r['count'] == 1

        # columns with data= option work fine
        assert r['email'] == 'foo@bar.org'

    # try to splice rows by index
    assert 'name' in stuff.rows[0]
    assert isinstance(stuff.rows[0:], list)

    # [bug] splicing the table gives as valid, working rows
    assert list(stuff[0]) == list(stuff.rows[0])
    assert stuff[0]['name'] == 'Foo Bar'

    # changing an instance's base_columns does not change the class
    assert id(stuff.base_columns) != id(StuffTable.base_columns)
    stuff.base_columns['test'] = tables.Column()
    assert not 'test' in StuffTable.base_columns

    # optionally, exceptions can be raised when input is invalid
    tables.options.IGNORE_INVALID_OPTIONS = False
    raises(Exception, "stuff.order_by = '-name,made-up-column'")
    raises(Exception, "stuff.order_by = ('made-up-column',)")
    # when a column name is overwritten, the original won't work anymore
    raises(Exception, "stuff.order_by = 'c'")
    # reset for future tests
    tables.options.IGNORE_INVALID_OPTIONS = True

def test_caches():
    """Ensure the various caches are effective.
    """

    class BookTable(tables.Table):
        name = tables.Column()
        answer = tables.Column(default=42)
    books = BookTable([
        {'name': 'Foo: Bar'},
    ])

    assert id(list(books.columns)[0]) == id(list(books.columns)[0])
    # TODO: row cache currently not used
    #assert id(list(books.rows)[0]) == id(list(books.rows)[0])

    # test that caches are reset after an update()
    old_column_cache = id(list(books.columns)[0])
    old_row_cache = id(list(books.rows)[0])
    books.update()
    assert id(list(books.columns)[0]) != old_column_cache
    assert id(list(books.rows)[0]) != old_row_cache

def test_sort():
    class BookTable(tables.Table):
        id = tables.Column()
        name = tables.Column()
        pages = tables.Column(name='num_pages')  # test rewritten names
        language = tables.Column(default='en')   # default affects sorting
        rating = tables.Column(data='*')         # test data field option

    books = BookTable([
        {'id': 1, 'pages':  60, 'name': 'Z: The Book', '*': 5},    # language: en
        {'id': 2, 'pages': 100, 'language': 'de', 'name': 'A: The Book', '*': 2},
        {'id': 3, 'pages':  80, 'language': 'de', 'name': 'A: The Book, Vol. 2', '*': 4},
        {'id': 4, 'pages': 110, 'language': 'fr', 'name': 'A: The Book, French Edition'},   # rating (with data option) is missing
    ])

    def test_order(order, result):
        books.order_by = order
        assert [b['id'] for b in books.rows] == result

    # None is normalized to an empty order by tuple, ensuring iterability;
    # it also supports all the cool methods that we offer for order_by.
    # This is true for the default case...
    assert books.order_by == ()
    iter(books.order_by)
    assert hasattr(books.order_by, 'reverse')
    # ...as well as when explicitly set to None.
    books.order_by = None
    assert books.order_by == ()
    iter(books.order_by)
    assert hasattr(books.order_by, 'reverse')

    # test various orderings
    test_order(('num_pages',), [1,3,2,4])
    test_order(('-num_pages',), [4,2,3,1])
    test_order(('name',), [2,4,3,1])
    test_order(('language', 'num_pages'), [3,2,1,4])
    # using a simple string (for convinience as well as querystring passing
    test_order('-num_pages', [4,2,3,1])
    test_order('language,num_pages', [3,2,1,4])
    # if overwritten, the declared fieldname has no effect
    test_order('pages,name', [2,4,3,1])   # == ('name',)
    # sort by column with "data" option
    test_order('rating', [4,2,3,1])

    # [bug] test alternative order formats if passed to constructor
    BookTable([], 'language,-num_pages')

    # test invalid order instructions
    books.order_by = 'xyz'
    assert not books.order_by
    books.base_columns['language'].sortable = False
    books.order_by = 'language'
    assert not books.order_by
    test_order(('language', 'num_pages'), [1,3,2,4])  # as if: 'num_pages'

    # [bug] order_by did not run through setter when passed to init
    books = BookTable([], order_by='name')
    assert books.order_by == ('name',)

def test_callable():
    """Data fields, ``default`` and ``data`` options can be callables.
    """

    class MathTable(tables.Table):
        lhs = tables.Column()
        rhs = tables.Column()
        op = tables.Column(default='+')
        sum = tables.Column(default=lambda d: calc(d['op'], d['lhs'], d['rhs']))
        sqrt = tables.Column(data=lambda d: int(sqrt(d['sum'])))

    math = MathTable([
        {'lhs': 1, 'rhs': lambda x: x['lhs']*3},              # 1+3
        {'lhs': 9, 'rhs': lambda x: x['lhs'], 'op': '/'},     # 9/9
        {'lhs': lambda x: x['rhs']+3, 'rhs': 4, 'op': '-'},   # 7-4
    ])

    # function is called when queried
    def calc(op, lhs, rhs):
        if op == '+': return lhs+rhs
        elif op == '/': return lhs/rhs
        elif op == '-': return lhs-rhs
    assert [calc(row['op'], row['lhs'], row['rhs']) for row in math] == [4,1,3]

    # field function is called while sorting
    math.order_by = ('-rhs',)
    assert [row['rhs'] for row in math] == [9,4,3]

    # default function is called while sorting
    math.order_by = ('sum',)
    assert [row['sum'] for row in math] == [1,3,4]

    # data function is called while sorting
    math.order_by = ('sqrt',)
    assert [row['sqrt'] for row in math] == [1,1,2]

def test_pagination():
    class BookTable(tables.Table):
        name = tables.Column()

    # create some sample data
    data = []
    for i in range(1,101):
        data.append({'name': 'Book Nr. %d'%i})
    books = BookTable(data)

    # external paginator
    paginator = Paginator(books.rows, 10)
    assert paginator.num_pages == 10
    page = paginator.page(1)
    assert len(page.object_list) == 10
    assert page.has_previous() == False
    assert page.has_next() == True

    # integrated paginator
    books.paginate(Paginator, 10, page=1)
    # rows is now paginated
    assert len(list(books.rows.page())) == 10
    assert len(list(books.rows.all())) == 100
    # new attributes
    assert books.paginator.num_pages == 10
    assert books.page.has_previous() == False
    assert books.page.has_next() == True