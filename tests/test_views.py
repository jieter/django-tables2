from math import ceil

import django_filters as filters
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase
from django.views.generic import TemplateView
from django_filters.views import FilterView

import django_tables2 as tables

from .app.models import Person, Region
from .utils import build_request

MEMORY_DATA = [
    {"name": "Queensland"},
    {"name": "New South Wales"},
    {"name": "Victoria"},
    {"name": "Tasmania"},
]


class SimpleTable(tables.Table):
    class Meta:
        model = Region
        exclude = ("id",)


class SimpleView(tables.SingleTableView):
    table_class = SimpleTable
    model = Region  # required for ListView


class SingleTableViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for region in MEMORY_DATA:
            Region.objects.create(name=region["name"])

    def test_should_support_pagination_options(self):
        class SimplePaginatedView(tables.SingleTableView):
            table_class = SimpleTable
            table_pagination = {"per_page": 1}
            model = Region

        response = SimplePaginatedView.as_view()(build_request())
        table = response.context_data["table"]
        self.assertEqual(table.paginator.num_pages, len(MEMORY_DATA))
        self.assertEqual(table.paginator.per_page, 1)

    def test_should_support_pagination_options_listView(self):
        class SimplePaginatedView(tables.SingleTableView):
            table_class = SimpleTable
            paginate_by = 1
            model = Region

        response = SimplePaginatedView.as_view()(build_request())
        table = response.context_data["table"]
        self.assertEqual(table.paginator.num_pages, len(MEMORY_DATA))
        self.assertEqual(table.paginator.per_page, 1)

    def test_should_support_default_pagination(self):
        total_records = 50
        for i in range(1, total_records + 1):
            Region.objects.create(name=f"region {i:02d} / {total_records}")

        expected_per_page = 25

        class PaginateDefault(tables.SingleTableMixin, TemplateView):
            table_class = SimpleTable
            template_name = "minimal.html"

            def get_table_data(self):
                return Region.objects.all()

        response = PaginateDefault.as_view()(build_request())
        response.render()
        table = response.context_data["table"]
        self.assertEqual(table.paginator.per_page, expected_per_page)
        self.assertEqual(table.paginator.num_pages, 3)
        self.assertEqual(len(table.page), expected_per_page)

        # add one for the header row.
        self.assertEqual(response.content.decode().count("<tr>"), expected_per_page + 1)

        # in addition to New South Wales, Queensland, Tasmania and Victoria,
        # 21 records should be displayed.
        self.assertContains(response, f"21 / {total_records}")
        self.assertNotContains(response, f"22 / {total_records}")

    def test_should_support_default_pagination_with_table_options(self):
        class Table(tables.Table):
            class Meta:
                model = Region
                per_page = 2

        class PaginateByDefinedOnView(tables.SingleTableView):
            table_class = Table
            model = Region
            table_data = MEMORY_DATA

        response = PaginateByDefinedOnView.as_view()(build_request())
        table = response.context_data["table"]
        self.assertEqual(table.paginator.per_page, 2)
        self.assertEqual(len(table.page), 2)

    def test_should_support_disabling_pagination_options(self):
        class SimpleNotPaginatedView(tables.SingleTableView):
            table_class = SimpleTable
            table_data = MEMORY_DATA
            table_pagination = False
            model = Region  # required for ListView

        response = SimpleNotPaginatedView.as_view()(build_request())
        table = response.context_data["table"]
        self.assertFalse(hasattr(table, "page"))

    def test_data_from_get_queryset(self):
        class GetQuerysetView(SimpleView):
            def get_queryset(self):
                return Region.objects.filter(name__startswith="Q")

        response = GetQuerysetView.as_view()(build_request())
        table = response.context_data["table"]

        self.assertEqual(len(table.rows), 1)
        self.assertEqual(table.rows[0].get_cell("name"), "Queensland")

    def test_should_support_explicit_table_data(self):
        class ExplicitDataView(tables.SingleTableView):
            table_class = SimpleTable
            table_pagination = {"per_page": 1}
            model = Region
            table_data = MEMORY_DATA

        response = ExplicitDataView.as_view()(build_request())
        table = response.context_data["table"]
        self.assertEqual(table.paginator.num_pages, len(MEMORY_DATA))

    def test_paginate_by_on_view_class(self):
        class Table(tables.Table):
            class Meta:
                model = Region

        class PaginateByDefinedOnView(tables.SingleTableView):
            table_class = Table
            model = Region
            paginate_by = 2
            table_data = MEMORY_DATA

            def get_queryset(self):
                return Region.objects.all().order_by("name")

        response = PaginateByDefinedOnView.as_view()(build_request())
        table = response.context_data["table"]
        self.assertEqual(table.paginator.per_page, 2)

    def test_with_custom_paginator(self):
        # defined in paginator_class
        class View(tables.SingleTableView):
            table_class = tables.Table
            queryset = Region.objects.all()
            paginator_class = tables.LazyPaginator

        response = View.as_view()(build_request())
        self.assertIsInstance(response.context_data["table"].paginator, tables.LazyPaginator)

        # defined in table_pagination
        class View(tables.SingleTableView):
            table_class = tables.Table
            queryset = Region.objects.all()
            table_pagination = {"paginator_class": tables.LazyPaginator}
            paginate_orphans = 10

        response = View.as_view()(build_request())
        paginator = response.context_data["table"].paginator
        self.assertIsInstance(paginator, tables.LazyPaginator)
        self.assertEqual(paginator.orphans, 10)

    def test_get_paginate_by_has_priority_over_paginate_by(self):
        class View(tables.SingleTableView):
            table_class = tables.Table
            queryset = Region.objects.all()
            # This paginate_by should be ignored because get_paginated_by is overridden
            paginate_by = 4

            def get_paginate_by(self, queryset):
                # Should paginate by 10
                return 10

        response = View.as_view()(build_request())
        self.assertEqual(response.context_data["table"].paginator.per_page, 10)

    def test_pass_queryset_to_get_paginate_by(self):
        # defined in paginator_class
        class View(tables.SingleTableView):
            table_class = tables.Table
            queryset = Region.objects.all()

            def get_paginate_by(self, table_data):
                # Should split table items into 2 pages
                return ceil(len(table_data) / 2)

        response = View.as_view()(build_request())
        self.assertEqual(response.context_data["table"].paginator.num_pages, 2)

    def test_should_pass_kwargs_to_table_constructor(self):
        class PassKwargsView(SimpleView):
            table_data = []

            def get_table(self, **kwargs):
                kwargs.update({"orderable": False})
                return super().get_table(**kwargs)

        response = SimpleView.as_view()(build_request("/"))
        self.assertTrue(response.context_data["table"].orderable)

        response = PassKwargsView.as_view()(build_request("/"))
        self.assertFalse(response.context_data["table"].orderable)

    def test_should_override_table_pagination(self):
        class PrefixedTable(SimpleTable):
            class Meta(SimpleTable.Meta):
                prefix = "p_"

        class PrefixedView(SimpleView):
            table_class = PrefixedTable

        class PaginationOverrideView(PrefixedView):
            table_data = MEMORY_DATA

            def get_table_pagination(self, table):
                assert isinstance(table, tables.Table)

                per_page = self.request.GET.get(f"{table.prefixed_per_page_field}_override")
                if per_page is not None:
                    return {"per_page": per_page}
                return super().get_table_pagination(table)

        response = PaginationOverrideView.as_view()(build_request("/?p_per_page_override=2"))
        self.assertEqual(response.context_data["table"].paginator.per_page, 2)

    def test_using_get_queryset(self):
        """
        Should not raise a value-error for a View using View.get_queryset().

        (test for reverting regressing in #423)
        """
        Person.objects.create(first_name="Anton", last_name="Sam")

        class Table(tables.Table):
            class Meta:
                model = Person
                fields = ("first_name", "last_name")

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
        self.assertEqual(table_class.__name__, "RegionAutogeneratedTable")

    def test_get_tables_class_raises_no_model(self):
        class Table(tables.SingleTableView):
            model = None
            table_class = None

        view = Table()
        message = "You must either specify Table.table_class or Table.model"
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            view.get_table_class()


class SingleTableMixinTest(TestCase):
    def test_with_non_paginated_view(self):
        """
        SingleTableMixin should not assume it is mixed with a ListView.

        Github issue #326
        """

        class Table(tables.Table):
            class Meta:
                model = Region

        class View(tables.SingleTableMixin, TemplateView):
            table_class = Table
            table_data = MEMORY_DATA

            template_name = "dummy.html"

        View.as_view()(build_request())

    def test_should_paginate_by_default(self):
        """When mixing SingleTableMixin with FilterView, the table should paginate by default."""
        total_records = 60
        for i in range(1, total_records + 1):
            Region.objects.create(name=f"region {i:02d} / {total_records}")

        expected_per_page = 25

        class RegionFilter(filters.FilterSet):
            name = filters.CharFilter(lookup_expr="icontains")

        class PaginateDefault(tables.SingleTableMixin, FilterView):
            table_class = SimpleTable
            model = Region
            filterset_class = RegionFilter
            template_name = "minimal.html"

        response = PaginateDefault.as_view()(build_request())
        response.render()
        table = response.context_data["table"]
        self.assertEqual(table.paginator.per_page, expected_per_page)
        self.assertEqual(table.paginator.num_pages, 3)
        self.assertEqual(len(table.page), expected_per_page)

        self.assertEqual(response.content.decode().count("<tr>"), expected_per_page + 1)


class TableA(tables.Table):
    class Meta:
        model = Person


class TableB(tables.Table):
    class Meta:
        model = Region
        exclude = ("id",)


class MultiTableMixinTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Person.objects.create(first_name="Jan Pieter", last_name="W")

        NL_PROVICES = (
            "Flevoland",
            "Friesland",
            "Gelderland",
            "Groningen",
            "Limburg",
            "Noord-Brabant",
            "Noord-Holland",
            "Overijssel",
            "Utrecht",
            "Zeeland",
            "Zuid-Holland",
        )
        for name in NL_PROVICES:
            Region.objects.create(name=name)

    def test_basic(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableA, TableB)
            tables_data = (Person.objects.all(), Region.objects.all())
            template_name = "multiple.html"

        response = View.as_view()(build_request("/"))
        response.render()

        html = response.rendered_content

        self.assertIn("table_0-sort=first_name", html)
        self.assertIn("table_1-sort=name", html)

        self.assertIn("<td >Jan Pieter</td>", html)
        self.assertIn("<td >Zuid-Holland</td>", html)

    def test_supplying_instances(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableA(Person.objects.all()), TableB(Region.objects.all()))
            template_name = "multiple.html"

        response = View.as_view()(build_request("/"))
        response.render()

        html = response.rendered_content

        self.assertIn("table_0-sort=first_name", html)
        self.assertIn("table_1-sort=name", html)

        self.assertIn("<td >Jan Pieter</td>", html)
        self.assertIn("<td >Zuid-Holland</td>", html)

    def test_without_tables(self):
        class View(tables.MultiTableMixin, TemplateView):
            template_name = "multiple.html"

        message = "No tables were specified. Define View.tables"
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            View.as_view()(build_request("/"))

    def test_with_empty_get_tables_list(self):
        class View(tables.MultiTableMixin, TemplateView):
            template_name = "multiple.html"

            def get_tables(self):
                return []

        response = View.as_view()(build_request("/"))
        response.render()

        html = response.rendered_content
        self.assertIn("<h1>Multiple tables using MultiTableMixin</h1>", html)

    def test_with_empty_class_tables_list(self):
        class View(tables.MultiTableMixin, TemplateView):
            template_name = "multiple.html"
            tables = []

        response = View.as_view()(build_request("/"))
        response.render()

        html = response.rendered_content
        self.assertIn("<h1>Multiple tables using MultiTableMixin</h1>", html)

    def test_length_mismatch(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableA, TableB)
            tables_data = (Person.objects.all(),)
            template_name = "multiple.html"

        message = "len(View.tables_data) != len(View.tables)"
        with self.assertRaisesMessage(ImproperlyConfigured, message):
            View.as_view()(build_request("/"))

    def test_table_pagination(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableB(Region.objects.all()), TableB(Region.objects.all()))
            template_name = "multiple.html"

            table_pagination = {"per_page": 5}

        response = View.as_view()(build_request("/?table_1-page=3"))

        tableA, tableB = response.context_data["tables"]
        self.assertEqual(tableA.page.number, 1)
        self.assertEqual(tableB.page.number, 3)

    def test_paginate_by(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableB(Region.objects.all()), TableB(Region.objects.all()))
            template_name = "multiple.html"

            paginate_by = 5

        response = View.as_view()(build_request("/?table_1-page=3"))

        tableA, tableB = response.context_data["tables"]
        self.assertEqual(tableA.page.number, 1)
        self.assertEqual(tableB.page.number, 3)

    def test_pass_table_data_to_get_paginate_by(self):
        class View(tables.MultiTableMixin, TemplateView):
            template_name = "multiple.html"
            tables = (TableB, TableB)
            tables_data = (Region.objects.all(), Region.objects.all())

            def get_paginate_by(self, table_data) -> int | None:
                # Split data into 3 pages
                return ceil(len(table_data) / 3)

        response = View.as_view()(build_request())

        for table in response.context_data["tables"]:
            self.assertEqual(table.paginator.num_pages, 3)

    def test_get_tables_data(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (TableA, TableB)
            template_name = "multiple.html"

            def get_tables_data(self):
                return [Person.objects.all(), Region.objects.all()]

        response = View.as_view()(build_request("/"))
        response.render()

        html = response.rendered_content

        self.assertIn("<td >Jan Pieter</td>", html)
        self.assertIn("<td >Zuid-Holland</td>", html)

    def test_table_prefix(self):
        class View(tables.MultiTableMixin, TemplateView):
            tables = (
                TableB(Region.objects.all(), prefix="test_prefix"),
                TableB(Region.objects.all()),
            )
            template_name = "multiple.html"

        response = View.as_view()(build_request("/"))

        tableA = response.context_data["tables"][0]
        tableB = response.context_data["tables"][1]

        self.assertEqual("test_prefix", tableA.prefix)
        self.assertIn("table", tableB.prefix)
