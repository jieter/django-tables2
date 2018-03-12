# coding: utf-8

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.test import TestCase
from django.views.generic.base import TemplateView

import django_tables2 as tables

from .app.models import Person, Region
from .utils import build_request

MEMORY_DATA = [
    {'name': 'Queensland'},
    {'name': 'New South Wales'},
    {'name': 'Victoria'},
    {'name': 'Tasmania'}
]


class DispatchHookMixin(object):
    '''
    Returns a response *and* reference to the view.
    '''
    def dispatch(self, *args, **kwargs):
        return super(DispatchHookMixin, self).dispatch(*args, **kwargs), self


class SimpleTable(tables.Table):
    class Meta:
        model = Region


class SimpleView(DispatchHookMixin, tables.SingleTableView):
    table_class = SimpleTable
    model = Region  # required for ListView


class SimplePaginatedView(DispatchHookMixin, tables.SingleTableView):
    table_class = SimpleTable
    table_pagination = {'per_page': 1}
    model = Region  # required for ListView


class SingleTableViewTest(TestCase):
    def test_should_support_pagination_options(self):
        for region in MEMORY_DATA:
            Region.objects.create(name=region['name'])

        response, view = SimplePaginatedView.as_view()(build_request('/'))
        self.assertEqual(view.get_table().paginator.num_pages, len(MEMORY_DATA))
        self.assertEqual(view.get_table().paginator.per_page, 1)

    def test_should_support_default_pagination(self):
        class PaginateDefault(DispatchHookMixin, tables.SingleTableView):
            table_class = SimpleTable
            model = Region
            table_data = MEMORY_DATA

        response, view = PaginateDefault.as_view()(build_request('/'))
        table = view.get_table()
        self.assertEqual(table.paginator.per_page, 25)
        self.assertEqual(len(table.page), 4)

    def test_should_support_default_pagination_with_table_options(self):
        class Table(tables.Table):
            class Meta:
                model = Region
                per_page = 2

        class PaginateByDefinedOnView(DispatchHookMixin, tables.SingleTableView):
            table_class = Table
            model = Region
            table_data = MEMORY_DATA

        response, view = PaginateByDefinedOnView.as_view()(build_request('/'))
        table = view.get_table()
        self.assertEqual(table.paginator.per_page, 2)
        self.assertEqual(len(table.page), 2)

    def test_should_support_disabling_pagination_options(self):
        class SimpleNotPaginatedView(DispatchHookMixin, tables.SingleTableView):
            table_class = SimpleTable
            table_data = MEMORY_DATA
            table_pagination = False
            model = Region  # required for ListView

        response, view = SimpleNotPaginatedView.as_view()(build_request('/'))
        table = view.get_table()
        self.assertFalse(hasattr(table, 'page'))

    def test_data_from_get_queryset(self):
        for region in MEMORY_DATA:
            Region.objects.create(name=region['name'])

        class GetQuerysetView(SimpleView):
            def get_queryset(self):
                return Region.objects.filter(name__startswith='Q')

        response, view = GetQuerysetView.as_view()(build_request('/'))
        table = view.get_table()

        self.assertEqual(len(table.rows), 1)
        self.assertEqual(table.rows[0].get_cell('name'), 'Queensland')

    def test_should_support_explicit_table_data(self):
        class ExplicitDataView(SimplePaginatedView):
            table_data = MEMORY_DATA

        response, view = ExplicitDataView.as_view()(build_request('/'))
        self.assertEqual(view.get_table().paginator.num_pages, len(MEMORY_DATA))

    def test_paginate_by_on_view_class(self):
        Region.objects.create(name='Friesland')

        class Table(tables.Table):
            class Meta:
                model = Region

        class PaginateByDefinedOnView(DispatchHookMixin, tables.SingleTableView):
            table_class = Table
            model = Region
            paginate_by = 2
            table_data = MEMORY_DATA

            def get_queryset(self):
                return Region.objects.all().order_by('name')

        response, view = PaginateByDefinedOnView.as_view()(build_request('/'))
        assert view.get_table().paginator.per_page == 2

    def test_should_pass_kwargs_to_table_constructor(self):
        class PassKwargsView(SimpleView):
            table_data = []

            def get_table(self, **kwargs):
                kwargs.update({'orderable': False})
                return super(PassKwargsView, self).get_table(**kwargs)

        response, view = SimpleView.as_view()(build_request('/'))
        assert view.get_table().orderable is True

        response, view = PassKwargsView.as_view()(build_request('/'))
        assert view.get_table().orderable is False

    def test_should_override_table_pagination(self):
        class PrefixedTable(SimpleTable):
            class Meta(SimpleTable.Meta):
                prefix = 'p_'

        class PrefixedView(SimpleView):
            table_class = PrefixedTable

        class PaginationOverrideView(PrefixedView):
            table_data = MEMORY_DATA

            def get_table_pagination(self, table):
                assert isinstance(table, tables.Table)

                per_page = self.request.GET.get('%s_override' % table.prefixed_per_page_field)
                if per_page is not None:
                    return {'per_page': per_page}
                return super(PaginationOverrideView, self).get_table_pagination(table)

        response, view = PaginationOverrideView.as_view()(build_request('/?p_per_page_override=2'))
        assert view.get_table().paginator.per_page == 2

    def test_using_get_queryset(self):
        '''
        Should not raise a value-error for a View using View.get_queryset()
        (test for reverting regressing in #423)
        '''
        Person.objects.create(first_name='Anton', last_name='Sam')

        class Table(tables.Table):
            class Meta(object):
                model = Person
                fields = ('first_name', 'last_name')

        class TestView(tables.SingleTableView):
            model = Person
            table_class = Table

            def get(self, request, *args, **kwargs):
                self.get_table()
                from django.http import HttpResponse
                return HttpResponse()

            def get_queryset(self):
                return Person.objects.all()

        TestView.as_view()(build_request())

    def test_get_tables_class(self):
        view = SimpleView()
        table_class = view.get_table_class()
        self.assertEqual(table_class, view.table_class)

    def test_get_tables_class_auto(self):
        class SimpleNoTableClassView(tables.SingleTableView):
            model = Region

        view = SimpleNoTableClassView()
        table_class = view.get_table_class()
        self.assertEqual(table_class.__name__, 'RegionTable')

    def test_get_tables_class_raises_no_model(self):
        class SimpleNoTableClassNoModelView(tables.SingleTableView):
            model = None
            table_class = None

        view = SimpleNoTableClassNoModelView()
        with self.assertRaises(ImproperlyConfigured):
            view.get_table_class()


class SingleTableMixinTest(TestCase):
    def test_with_non_paginated_view(self):
        '''
        SingleTableMixin should not assume it is mixed with a ListView

        Github issue #326
        '''

        class Table(tables.Table):
            class Meta:
                model = Region

        class View(tables.SingleTableMixin, TemplateView):
            table_class = Table
            table_data = MEMORY_DATA

            template_name = 'dummy.html'

        View.as_view()(build_request())

    def test_with_custom_paginator(self):
        class Table(tables.Table):
            class Meta:
                model = Region

        class MyPaginator(Paginator):
            pass

        class View(DispatchHookMixin, tables.SingleTableView):
            table_class = Table
            queryset = Region.objects.all()
            table_pagination = {
                'klass': MyPaginator
            }

        response, view = View.as_view()(build_request())

        context = view.get_context_data()
        self.assertIsInstance(context['table'].paginator, MyPaginator)


class TableA(tables.Table):
    class Meta:
        model = Person


class TableB(tables.Table):
    class Meta:
        model = Region
        exclude = ('id', )


class MultiTableMixinTest(TestCase):
    def setUp(self):
        Person.objects.create(first_name='Jan Pieter', last_name='W')

        NL_PROVICES = (
            'Flevoland', 'Friesland', 'Gelderland', 'Groningen', 'Limburg',
            'Noord-Brabant', 'Noord-Holland', 'Overijssel', 'Utrecht',
            'Zeeland', 'Zuid-Holland',
        )
        for name in NL_PROVICES:
            Region.objects.create(name=name)

    def test_basic(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableA, TableB)
            tables_data = (Person.objects.all(), Region.objects.all())
            template_name = 'multiple.html'

        response = View.as_view()(build_request('/'))
        response.render()

        html = response.rendered_content

        assert 'table_0-sort=first_name' in html
        assert 'table_1-sort=name' in html

        assert '<td class="first_name">Jan Pieter</td>' in html
        assert '<td class="name">Zuid-Holland</td>' in html

    def test_supplying_instances(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (
                TableA(Person.objects.all()),
                TableB(Region.objects.all())
            )
            template_name = 'multiple.html'

        response = View.as_view()(build_request('/'))
        response.render()

        html = response.rendered_content

        assert 'table_0-sort=first_name' in html
        assert 'table_1-sort=name' in html

        assert '<td class="first_name">Jan Pieter</td>' in html
        assert '<td class="name">Zuid-Holland</td>' in html

    def test_without_tables(self):
        class View(tables.MultiTableMixin, TemplateView):
            template_name = 'multiple.html'

        with self.assertRaises(ImproperlyConfigured):
            View.as_view()(build_request('/'))

    def test_with_empty_get_tables_list(self):
        class View(tables.MultiTableMixin, TemplateView):
            template_name = 'multiple.html'

            def get_tables(self):
                return []

        response = View.as_view()(build_request('/'))
        response.render()

        html = response.rendered_content
        assert '<h1>Multiple tables using MultiTableMixin</h1>' in html

    def test_length_mismatch(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableA, TableB)
            tables_data = (Person.objects.all(), )
            template_name = 'multiple.html'

        with self.assertRaises(ImproperlyConfigured):
            View.as_view()(build_request('/'))

    def test_pagination(self):
        class View(DispatchHookMixin, tables.MultiTableMixin, TemplateView):
            tables = (
                TableB(Region.objects.all()),
                TableB(Region.objects.all())
            )
            template_name = 'multiple.html'

            table_pagination = {
                'per_page': 5
            }

        response, view = View.as_view()(build_request('/?table_1-page=3'))

        tableA, tableB = view.get_tables()

        assert tableA.page.number == 1
        assert tableB.page.number == 3

    def test_get_tables_data(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableA, TableB)
            template_name = 'multiple.html'

            def get_tables_data(self):
                return [Person.objects.all(), Region.objects.all()]

        response = View.as_view()(build_request('/'))
        response.render()

        html = response.rendered_content

        assert '<td class="first_name">Jan Pieter</td>' in html
        assert '<td class="name">Zuid-Holland</td>' in html
