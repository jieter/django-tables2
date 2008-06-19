"""Test the base table functionality.

This includes the core, as well as static data, non-model tables.
"""

from py.test import raises
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
    class BookTable(tables.Table):
        name = tables.Column()
        answer = tables.Column(default=42)
        c = tables.Column(name="count", default=1)
    books = BookTable([
        {'id': 1, 'name': 'Foo: Bar'},
    ])

    # access without order_by works
    books.data
    books.rows

    # make sure BoundColumnn.name always gives us the right thing, whether
    # the column explicitely defines a name or not.
    books.columns['count'].name == 'count'
    books.columns['answer'].name == 'answer'

    for r in books.rows:
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

    # changing an instance's base_columns does not change the class
    assert id(books.base_columns) != id(BookTable.base_columns)
    books.base_columns['test'] = tables.Column()
    assert not 'test' in BookTable.base_columns

    # optionally, exceptions can be raised when input is invalid
    tables.options.IGNORE_INVALID_OPTIONS = False
    raises(Exception, "books.order_by = '-name,made-up-column'")
    raises(Exception, "books.order_by = ('made-up-column',)")
    # when a column name is overwritten, the original won't work anymore
    raises(Exception, "books.order_by = 'c'")
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
        language = tables.Column(default='en')  # default affects sorting

    books = BookTable([
        {'id': 1, 'pages':  60, 'name': 'Z: The Book'},    # language: en
        {'id': 2, 'pages': 100, 'language': 'de', 'name': 'A: The Book'},
        {'id': 3, 'pages':  80, 'language': 'de', 'name': 'A: The Book, Vol. 2'},
        {'id': 4, 'pages': 110, 'language': 'fr', 'name': 'A: The Book, French Edition'},
    ])

    def test_order(order, result):
        books.order_by = order
        assert [b['id'] for b in books.data] == result

    # test various orderings
    test_order(('num_pages',), [1,3,2,4])
    test_order(('-num_pages',), [4,2,3,1])
    test_order(('name',), [2,4,3,1])
    test_order(('language', 'num_pages'), [3,2,1,4])
    # using a simple string (for convinience as well as querystring passing
    test_order('-num_pages', [4,2,3,1])
    test_order('language,num_pages', [3,2,1,4])
    # TODO: test that unrewritte name has no effect

    # [bug] test alternative order formats if passed to constructor
    BookTable([], 'language,-num_pages')

    # test invalid order instructions
    books.order_by = 'xyz'
    assert not books.order_by
    books.base_columns['language'].sortable = False
    books.order_by = 'language'
    assert not books.order_by
    test_order(('language', 'num_pages'), [1,3,2,4])  # as if: 'num_pages'