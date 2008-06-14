"""Test template specific functionality.

Make sure tables expose their functionality to templates right.
"""

import django_tables as tables

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