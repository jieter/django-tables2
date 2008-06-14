from django.core.paginator import Paginator
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

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

    # test more with actual models

def test_basic():
    class BookTable(tables.Table):
        name = tables.Column()
    books = BookTable([
        {'id': 1, 'name': 'Foo: Bar'},
    ])
    # access without order_by works
    books.data
    # unknown fields are removed
    for d in books.data:
        assert not 'id' in d

def test_sort():
    class BookTable(tables.Table):
        id = tables.Column()
        name = tables.Column()
        pages = tables.Column()
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
    test_order(('pages',), [1,3,2,4])
    test_order(('-pages',), [4,2,3,1])
    test_order(('name',), [2,4,3,1])
    test_order(('language', 'pages'), [3,2,1,4])
    # using a simple string (for convinience as well as querystring passing
    test_order('-pages', [4,2,3,1])
    test_order('language,pages', [3,2,1,4])

    # [bug] test alternative order formats if passed to constructor
    BookTable([], 'language,-pages')

    # test invalid order instructions
    books.order_by = 'xyz'
    assert not books.order_by
    books.columns['language'].sortable = False
    books.order_by = 'language'
    assert not books.order_by
    test_order(('language', 'pages'), [1,3,2,4])  # as if: 'pages'

def test_for_templates():
    class BookTable(tables.Table):
        id = tables.Column()
        name = tables.Column()
    books = BookTable([
        {'id': 1, 'name': 'Foo: Bar'},
    ])

    # cast to a string we get a value ready to be passed to the querystring
    books.order_by = ('name',)
    assert str(books.order_by) == 'name'
    books.order_by = ('name', '-id')
    assert str(books.order_by) == 'name,-id'

test_declaration()
test_basic()
test_sort()
test_for_templates()


"""
<table>
<tr>
    {% for column in book.columns %}
        <th><a href="{{ column.name }}">{{ column }}</a></th
        <th><a href="{% set_url_param "sort" column.name }}">{{ column }}</a></th
    {% endfor %}
</tr>
{% for row in book %}
    <tr>
        {% for value in row %}
            <td>{{ value }]</td>
        {% endfor %}
    </tr>
{% endfor %}
</table>

OR:

<table>
{% for row in book %}
    <tr>
        {% if book.columns.name.visible %}
            <td>{{ row.name }]</td>
        {% endif %}
        {% if book.columns.score.visible %}
            <td>{{ row.score }]</td>
        {% endif %}
    </tr>
{% endfor %}
</table>


"""