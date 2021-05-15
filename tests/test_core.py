"""Test the core table functionality."""

import copy
import itertools

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils.translation import gettext_lazy, override

import django_tables2 as tables
from django_tables2.tables import DeclarativeColumnsMetaclass

from .app.models import Occupation, Person
from .utils import build_request, parse

request = build_request("/")

MEMORY_DATA = [
    {"i": 2, "alpha": "b", "beta": "b"},
    {"i": 1, "alpha": "a", "beta": "c"},
    {"i": 3, "alpha": "c", "beta": "a"},
]


class UnorderedTable(tables.Table):
    i = tables.Column()
    alpha = tables.Column()
    beta = tables.Column()


class CoreTest(SimpleTestCase):
    def test_omitting_data(self):
        with self.assertRaises(TypeError):
            UnorderedTable()

    def test_column_named_items(self):
        """A column named items must not make the table fail."""
        # https://github.com/bradleyayers/django-tables2/issues/316

        class ItemsTable(tables.Table):
            items = tables.Column()

        table = ItemsTable([{"items": 123}, {"items": 2345}])

        html = table.as_html(request)
        self.assertIn("123", html)
        self.assertIn("2345", html)

    def test_declarations(self):
        """Test defining tables by declaration."""

        class GeoAreaTable(tables.Table):
            name = tables.Column()
            population = tables.Column()

        self.assertEqual(len(GeoAreaTable.base_columns), 2)
        self.assertIn("name", GeoAreaTable.base_columns)
        self.assertFalse(hasattr(GeoAreaTable, "name"))

        class CountryTable(GeoAreaTable):
            capital = tables.Column()

        self.assertEqual(len(CountryTable.base_columns), 3)
        self.assertIn("capital", CountryTable.base_columns)

        # multiple inheritance
        class AddedMixin(tables.Table):
            added = tables.Column()

        class CityTable(GeoAreaTable, AddedMixin):
            mayor = tables.Column()

        self.assertEqual(len(CityTable.base_columns), 4)
        self.assertIn("added", CityTable.base_columns)

        # overwrite a column with a non-column
        class MayorlessCityTable(CityTable):
            mayor = None

        self.assertEqual(len(MayorlessCityTable.base_columns), 3)

    def test_metaclass_inheritance(self):
        class Tweaker(type):
            """Adds an attribute "tweaked" to all classes"""

            def __new__(cls, name, bases, attrs):
                attrs["tweaked"] = True
                return super().__new__(cls, name, bases, attrs)

        class Meta(Tweaker, DeclarativeColumnsMetaclass):
            pass

        class TweakedTableBase(tables.Table):
            __metaclass__ = Meta
            name = tables.Column()

        TweakedTable = Meta("TweakedTable", (TweakedTableBase,), {})

        table = TweakedTable([])
        self.assertIn("name", table.columns)
        self.assertTrue(table.tweaked)

        # now flip the order
        class FlippedMeta(DeclarativeColumnsMetaclass, Tweaker):
            pass

        class FlippedTweakedTableBase(tables.Table):
            name = tables.Column()

        FlippedTweakedTable = FlippedMeta("FlippedTweakedTable", (FlippedTweakedTableBase,), {})

        table = FlippedTweakedTable([])
        self.assertIn("name", table.columns)
        self.assertTrue(table.tweaked)

    def test_Meta_attribute_incorrect_types(self):
        with self.assertRaises(TypeError):

            class MetaTable1(tables.Table):
                class Meta:
                    exclude = "foo"

        with self.assertRaises(TypeError):

            class MetaTable2(tables.Table):
                class Meta:
                    sequence = "..."

        with self.assertRaises(TypeError):

            class MetaTable3(tables.Table):
                class Meta:
                    model = {}

    def test_table_attrs(self):
        class TestTable(tables.Table):
            class Meta:
                attrs = {}

        self.assertEqual(TestTable([]).attrs.as_html(), "")

        class TestTable2(tables.Table):
            class Meta:
                attrs = {"a": "b"}

        self.assertEqual(TestTable2([]).attrs.as_html(), 'a="b"')

        class TestTable3(tables.Table):
            pass

        self.assertEqual(TestTable3([]).attrs.as_html(), "")
        self.assertEqual(TestTable3([], attrs={"a": "b"}).attrs.as_html(), 'a="b"')

        class TestTable4(tables.Table):
            class Meta:
                attrs = {"a": "b"}

        self.assertEqual(TestTable4([], attrs={"c": "d"}).attrs.as_html(), 'c="d"')

    def test_attrs_support_computed_values(self):
        counter = itertools.count()

        class TestTable(tables.Table):
            class Meta:
                attrs = {"id": lambda: "test_table_%d" % next(counter)}

        self.assertEqual('id="test_table_0"', TestTable([]).attrs.as_html())
        self.assertEqual('id="test_table_1"', TestTable([]).attrs.as_html())

    @override_settings(DJANGO_TABLES2_TABLE_ATTRS={"class": "table-compact"})
    def test_attrs_from_settings(self):
        class Table(tables.Table):
            pass

        table = Table({})
        self.assertEqual(table.attrs.as_html(), 'class="table-compact"')

    def test_table_attrs_thead_tbody_tfoot(self):
        class Table(tables.Table):
            column = tables.Column(footer="foo")

            class Meta:
                attrs = {
                    "class": "table-class",
                    "thead": {"class": "thead-class"},
                    "tbody": {"class": "tbody-class"},
                    "tfoot": {"class": "tfoot-class"},
                }

        html = Table([]).as_html(build_request())
        self.assertIn('<table class="table-class">', html)
        self.assertIn('<thead class="thead-class">', html)
        self.assertIn('<tbody class="tbody-class">', html)
        self.assertIn('<tfoot class="tfoot-class">', html)

    def test_datasource_untouched(self):
        """Ensure that data the data datasource is not modified by table operations."""
        original_data = copy.deepcopy(MEMORY_DATA)

        table = UnorderedTable(MEMORY_DATA)
        table.order_by = "i"
        list(table.rows)
        self.assertEqual(MEMORY_DATA, original_data)

        table = UnorderedTable(MEMORY_DATA)
        table.order_by = "beta"
        list(table.rows)
        self.assertEqual(MEMORY_DATA, original_data)

    def test_should_support_tuple_data_source(self):
        class SimpleTable(tables.Table):
            name = tables.Column()

        table = SimpleTable(({"name": "brad"}, {"name": "davina"}))

        self.assertEqual(len(table.rows), 2)

    def test_column_count(self):
        class SimpleTable(tables.Table):
            visible = tables.Column(visible=True)
            hidden = tables.Column(visible=False)

        # The columns container supports the len() builtin
        self.assertEqual(len(SimpleTable([]).columns), 1)

    def test_column_accessor(self):
        class SimpleTable(UnorderedTable):
            col1 = tables.Column(accessor="alpha__upper__isupper")
            col2 = tables.Column(accessor="alpha__upper")

        table = SimpleTable(MEMORY_DATA)

        self.assertTrue(table.rows[0].get_cell("col1"))
        self.assertEqual(table.rows[0].get_cell("col2"), "B")

    def test_exclude_columns(self):
        """
        Defining ``Table.Meta.exclude`` or providing an ``exclude`` argument when
        instantiating a table should have the same effect -- exclude those columns
        from the table. It should have the same effect as not defining the
        columns originally.
        """
        table = UnorderedTable([], exclude=("i"))
        self.assertEqual(table.columns.names(), ["alpha", "beta"])

        # Table.Meta: exclude=...
        class PartialTable(UnorderedTable):
            class Meta:
                exclude = ("alpha",)

        table = PartialTable([])
        self.assertEqual(table.columns.names(), ["i", "beta"])

        # Inheritence -- exclude in parent, add in child
        class AddonTable(PartialTable):
            added = tables.Column()

        table = AddonTable([])
        self.assertEqual(table.columns.names(), ["i", "beta", "added"])

        # Inheritence -- exclude in child
        class ExcludeTable(UnorderedTable):
            added = tables.Column()

            class Meta:
                exclude = ("beta",)

        table = ExcludeTable([])
        self.assertEqual(table.columns.names(), ["i", "alpha", "added"])

    def test_table_exclude_property_should_override_constructor_argument(self):
        class SimpleTable(tables.Table):
            a = tables.Column()
            b = tables.Column()

        table = SimpleTable([], exclude=("b",))
        self.assertEqual(table.columns.names(), ["a"])
        table.exclude = ("a",)
        self.assertEqual(table.columns.names(), ["b"])

    def test_exclude_should_work_on_sequence_too(self):
        """It should be possible to define a sequence on a table and exclude it in a child of that table."""

        class PersonTable(tables.Table):
            first_name = tables.Column()
            last_name = tables.Column()
            occupation = tables.Column()

            class Meta:
                sequence = ("first_name", "last_name", "occupation")

        class AnotherPersonTable(PersonTable):
            class Meta(PersonTable.Meta):
                exclude = ("first_name", "last_name")

        tableA = PersonTable([])
        self.assertEqual(tableA.columns.names(), ["first_name", "last_name", "occupation"])

        tableB = AnotherPersonTable([])
        self.assertEqual(tableB.columns.names(), ["occupation"])

        tableC = PersonTable([], exclude=("first_name"))
        self.assertEqual(tableC.columns.names(), ["last_name", "occupation"])

    def test_pagination(self):
        class BookTable(tables.Table):
            name = tables.Column()

        # create some sample data
        data = list([{"name": "Book No. %d" % i} for i in range(100)])
        books = BookTable(data)

        # external paginator
        paginator = Paginator(books.rows, 10)
        self.assertEqual(paginator.num_pages, 10)
        page = paginator.page(1)
        self.assertFalse(page.has_previous())
        self.assertTrue(page.has_next())

        # integrated paginator
        books.paginate(page=1)
        self.assertTrue(hasattr(books, "page"))

        books.paginate(page=1, per_page=10)
        self.assertEqual(len(list(books.page.object_list)), 10)

        # new attributes
        self.assertEqual(books.paginator.num_pages, 10)
        self.assertFalse(books.page.has_previous())
        self.assertTrue(books.page.has_next())

        # accessing a non-existant page raises 404
        with self.assertRaises(EmptyPage):
            books.paginate(Paginator, page=9999, per_page=10)

        with self.assertRaises(PageNotAnInteger):
            books.paginate(Paginator, page="abc", per_page=10)

    def test_pagination_shouldnt_prevent_multiple_rendering(self):
        class SimpleTable(tables.Table):
            name = tables.Column()

        table = SimpleTable([{"name": "brad"}])
        table.paginate()

        self.assertEqual(table.as_html(request), table.as_html(request))

    def test_empty_text(self):
        class TestTable(tables.Table):
            a = tables.Column()

        table = TestTable([])
        self.assertEqual(table.empty_text, None)

        class TestTable2(tables.Table):
            a = tables.Column()

            class Meta:
                empty_text = "nothing here"

        table = TestTable2([])
        self.assertEqual(table.empty_text, "nothing here")

        table = TestTable2([], empty_text="still nothing")
        self.assertEqual(table.empty_text, "still nothing")

    def test_empty_text_gettext_lazy(self):
        class TestTable(tables.Table):
            a = tables.Column()

            class Meta:
                empty_text = gettext_lazy("next")

        table = TestTable([])
        self.assertEqual(table.empty_text, "next")

        with override("nl"):
            table = TestTable([])
            self.assertEqual(table.empty_text, "volgende")

    def test_prefix(self):
        """Verify table prefixes affect the names of querystring parameters."""

        class TableA(tables.Table):
            name = tables.Column()

            class Meta:
                prefix = "x"

        table = TableA([])
        html = table.as_html(build_request("/"))

        self.assertEqual("x", table.prefix)
        self.assertIn("xsort=name", html)

        class TableB(tables.Table):
            last_name = tables.Column()

        self.assertEqual("", TableB([]).prefix)
        self.assertEqual("x", TableB([], prefix="x").prefix)

        table = TableB([])
        table.prefix = "x-"
        html = table.as_html(build_request("/"))

        self.assertEqual("x-", table.prefix)
        self.assertIn("x-sort=last_name", html)

    def test_field_names(self):
        class TableA(tables.Table):
            class Meta:
                order_by_field = "abc"
                page_field = "def"
                per_page_field = "ghi"

        table = TableA([])
        self.assertEqual("abc", table.order_by_field)
        self.assertEqual("def", table.page_field)
        self.assertEqual("ghi", table.per_page_field)

    def test_field_names_with_prefix(self):
        class TableA(tables.Table):
            class Meta:
                order_by_field = "sort"
                page_field = "page"
                per_page_field = "per_page"
                prefix = "1-"

        table = TableA([])
        self.assertEqual("1-sort", table.prefixed_order_by_field)
        self.assertEqual("1-page", table.prefixed_page_field)
        self.assertEqual("1-per_page", table.prefixed_per_page_field)

        class TableB(tables.Table):
            class Meta:
                order_by_field = "sort"
                page_field = "page"
                per_page_field = "per_page"

        table = TableB([], prefix="1-")
        self.assertEqual("1-sort", table.prefixed_order_by_field)
        self.assertEqual("1-page", table.prefixed_page_field)
        self.assertEqual("1-per_page", table.prefixed_per_page_field)

        table = TableB([])
        table.prefix = "1-"
        self.assertEqual("1-sort", table.prefixed_order_by_field)
        self.assertEqual("1-page", table.prefixed_page_field)
        self.assertEqual("1-per_page", table.prefixed_per_page_field)

    def test_should_support_a_template_name_to_be_specified(self):
        class ConstructorSpecifiedTemplateTable(tables.Table):
            name = tables.Column()

        table = ConstructorSpecifiedTemplateTable([], template_name="dummy.html")
        self.assertEqual(table.template_name, "dummy.html")

        class PropertySpecifiedTemplateTable(tables.Table):
            name = tables.Column()

        table = PropertySpecifiedTemplateTable([])
        table.template_name = "dummy.html"
        self.assertEqual(table.template_name, "dummy.html")

        class DefaultTable(tables.Table):
            pass

        table = DefaultTable([])
        self.assertEqual(table.template_name, "django_tables2/table.html")

    def test_template_name_in_meta_class_declaration_should_be_honored(self):
        class MetaDeclarationSpecifiedTemplateTable(tables.Table):
            name = tables.Column()

            class Meta:
                template_name = "dummy.html"

        table = MetaDeclarationSpecifiedTemplateTable([])
        self.assertEqual(table.template_name, "dummy.html")
        self.assertEqual(table.as_html(request), "dummy template contents\n")

    def test_should_support_rendering_multiple_times(self):
        class MultiRenderTable(tables.Table):
            name = tables.Column()

        # test list data
        table = MultiRenderTable([{"name": "brad"}])
        self.assertEqual(table.as_html(request), table.as_html(request))

    def test_column_defaults_are_honored(self):
        class Table(tables.Table):
            name = tables.Column(default="abcd")

            class Meta:
                default = "efgh"

        table = Table([{}], default="ijkl")
        self.assertEqual(table.rows[0].get_cell("name"), "abcd")

    def test_table_meta_defaults_are_honored(self):
        class Table(tables.Table):
            name = tables.Column()

            class Meta:
                default = "abcd"

        table = Table([{}])
        self.assertEqual(table.rows[0].get_cell("name"), "abcd")

    def test_table_defaults_are_honored(self):
        class Table(tables.Table):
            name = tables.Column()

        table = Table([{}], default="abcd")
        self.assertEqual(table.rows[0].get_cell("name"), "abcd")

        table = Table([{}], default="abcd")
        table.default = "efgh"
        self.assertEqual(table.rows[0].get_cell("name"), "efgh")


class BoundColumnTest(SimpleTestCase):
    def test_attrs_bool_error(self):
        class Table(tables.Table):
            c_element = tables.Column()

        class ErrorObject:
            def __bool__(self):
                raise NotImplementedError

        table = Table([{"c_element": ErrorObject()}])
        list(table.rows[0].items())
        try:
            table.columns[0].attrs
        except NotImplementedError:
            self.fail("__bool__ should not be evaluated!")

    def test_attrs_falsy_object(self):
        """Computed attrs in BoundColumn should be passed the column value, even if its __bool__ returns False."""

        class Table(tables.Table):
            c_element = tables.Column()

            class Meta:
                attrs = {"td": {"data-column-name": lambda value: value.name}}

        class FalsyObject:
            name = "FalsyObject1"

            def __bool__(self):
                return False

        table = Table([{"c_element": FalsyObject()}])
        list(table.rows[0].items())
        self.assertEqual("FalsyObject1", table.columns[0].attrs["td"]["data-column-name"])


class AsValuesTest(TestCase):
    AS_VALUES_DATA = [
        {"name": "Adrian", "country": "Australia"},
        {"name": "Adrian", "country": "Brazil"},
        {"name": "Audrey", "country": "Chile"},
        {"name": "Bassie", "country": "Belgium"},
    ]

    def test_as_values(self):
        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column()

        expected = [["Name", "Country"]] + [[r["name"], r["country"]] for r in self.AS_VALUES_DATA]
        table = Table(self.AS_VALUES_DATA)

        self.assertEqual(list(table.as_values()), expected)

    def test_as_values_exclude(self):
        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column()

        expected = [["Name"]] + [[r["name"]] for r in self.AS_VALUES_DATA]
        table = Table(self.AS_VALUES_DATA)

        self.assertEqual(list(table.as_values(exclude_columns=("country",))), expected)

    def test_as_values_exclude_from_export(self):
        class Table(tables.Table):
            name = tables.Column()
            buttons = tables.Column(exclude_from_export=True)

        self.assertEqual(list(Table([]).as_values()), [["Name"]])

    def test_as_values_visible_False(self):
        class Table(tables.Table):
            name = tables.Column()
            website = tables.Column(visible=False)

        self.assertEqual(list(Table([]).as_values()), [["Name", "Website"]])

    def test_as_values_empty_values(self):
        """Table's as_values() method returns `None` for missing values."""

        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column()

        data = [
            {"name": "Adrian", "country": "Brazil"},
            {"name": "Audrey"},
            {"name": "Bassie", "country": "Belgium"},
            {"country": "France"},
        ]
        expected = [["Name", "Country"]] + [[r.get("name"), r.get("country")] for r in data]
        table = Table(data)
        self.assertEqual(list(table.as_values()), expected)

    def test_render_FOO_exception(self):

        message = "Custom render-method fails"

        class Table(tables.Table):
            country = tables.Column()

            def render_country(self, value):
                raise Exception(message)
                return value + " test"

        with self.assertRaisesMessage(Exception, message):
            Table(self.AS_VALUES_DATA).as_html(build_request())

    def test_as_values_render_FOO(self):
        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column()

            def render_country(self, value):
                return value + " test"

        expected = [["Name", "Country"]] + [
            [r["name"], r["country"] + " test"] for r in self.AS_VALUES_DATA
        ]

        self.assertEqual(list(Table(self.AS_VALUES_DATA).as_values()), expected)

    def test_as_values_value_FOO(self):
        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column()

            def render_country(self, value):
                return value + " test"

            def value_country(self, value):
                return value + " different"

        expected = [["Name", "Country"]] + [
            [r["name"], r["country"] + " different"] for r in self.AS_VALUES_DATA
        ]

        self.assertEqual(list(Table(self.AS_VALUES_DATA).as_values()), expected)

    def test_as_values_accessor_relation(self):
        programmer = Occupation.objects.create(name="Programmer")
        henk = Person.objects.create(
            first_name="Henk", last_name="Voornaman", occupation=programmer
        )

        class Table(tables.Table):
            name = tables.Column(accessor=tables.A("first_name"))
            occupation = tables.Column(
                accessor=tables.A("occupation__name"), verbose_name="Occupation"
            )

        expected = [["First name", "Occupation"], [henk.first_name, programmer.name]]

        self.assertEqual(list(Table(Person.objects.all()).as_values()), expected)


class RowAttrsTest(SimpleTestCase):
    def test_row_attrs(self):
        class Table(tables.Table):
            alpha = tables.Column()
            beta = tables.Column()

        table = Table(
            MEMORY_DATA, row_attrs={"class": lambda table, record: "row-id-{}".format(record["i"])}
        )

        self.assertEqual(table.rows[0].attrs, {"class": "row-id-2 even"})

    def test_row_attrs_in_meta(self):
        class Table(tables.Table):
            alpha = tables.Column()
            beta = tables.Column()

            class Meta:
                row_attrs = {"class": lambda record: "row-id-{}".format(record["i"])}

        table = Table(MEMORY_DATA)
        self.assertEqual(table.rows[0].attrs, {"class": "row-id-2 even"})

    def test_td_attrs_from_table(self):
        class Table(tables.Table):
            alpha = tables.Column()
            beta = tables.Column()

            class Meta:
                attrs = {"td": {"data-column-name": lambda bound_column: bound_column.name}}

        table = Table(MEMORY_DATA)
        html = table.as_html(request)
        td = parse(html).find(".//tbody/tr[1]/td[1]")
        self.assertEqual(td.attrib, {"data-column-name": "alpha"})
