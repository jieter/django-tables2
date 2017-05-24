import itertools

import django_tables2 as tables

from .utils import build_request

TEST_DATA = [
    {'name': 'Belgium', 'population': 11200000},
    {'name': 'Luxembourgh', 'population': 540000},
    {'name': 'France', 'population': 66000000},
]


def _test_counter(Table, expected='<td class="counter">0</td>'):
    table = Table(TEST_DATA)
    html = table.as_html(build_request())
    assert expected in html

    # the counter should start at zero the second time too
    table = Table(TEST_DATA)
    html = table.as_html(build_request())
    assert expected in html

    return html


def test_row_counter_using_render_method():
    class CountryTable(tables.Table):
        counter = tables.Column(empty_values=(), orderable=False)
        name = tables.Column()

        def render_counter(self):
            self.row_counter = getattr(self, 'row_counter', itertools.count())
            return next(self.row_counter)

    _test_counter(CountryTable)


def test_row_counter_special_column():
    class CounterColumn(tables.Column):
        def __init__(self, *args, **kwargs):
            self.counter = itertools.count()
            kwargs.update({
                'empty_values': (),
                'orderable': False
            })
            super(CounterColumn, self).__init__(*args, **kwargs)

        def render(self):
            return next(self.counter)

    class CountryTable(tables.Table):
        counter = CounterColumn()
        name = tables.Column()

    _test_counter(CountryTable)


def test_row_footer_total():
    class CountryTable(tables.Table):
        name = tables.Column()
        population = tables.Column(
            footer=lambda table: 'Total: {}'.format(
                sum(x['population'] for x in table.data)
            )
        )

    table = CountryTable(TEST_DATA)
    html = table.as_html(build_request())

    assert '<td>Total: 77740000</td>' in html
