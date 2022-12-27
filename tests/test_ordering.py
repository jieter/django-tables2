from datetime import datetime

from django.test import TestCase

import django_tables2 as tables
from django_tables2 import RequestConfig

from .app.models import Person
from .utils import build_request

request = build_request("/")


MEMORY_DATA = [
    {"i": 2, "alpha": "b", "beta": "b"},
    {"i": 1, "alpha": "a", "beta": "c"},
    {"i": 3, "alpha": "c", "beta": "a"},
]

PEOPLE = [
    {"first_name": "Bradley", "last_name": "Ayers"},
    {"first_name": "Bradley", "last_name": "Fake"},
    {"first_name": "Chris", "last_name": "Doble"},
    {"first_name": "Davina", "last_name": "Adisusila"},
    {"first_name": "Ross", "last_name": "Ayers"},
]


class UnorderedTable(tables.Table):
    i = tables.Column()
    alpha = tables.Column()
    beta = tables.Column()


class OrderedTable(UnorderedTable):
    class Meta:
        order_by = "alpha"


class OrderingTest(TestCase):
    def test_meta_ordering_list(self):
        class Table(UnorderedTable):
            class Meta:
                order_by = ["i", "alpha"]

        self.assertEqual(Table([]).order_by, ("i", "alpha"))
        self.assertEqual(Table([], order_by=["alpha", "i"]).order_by, ("alpha", "i"))

    def test_meta_ordering_tuple(self):
        class Table(UnorderedTable):
            class Meta:
                order_by = ("i", "alpha")

        self.assertEqual(Table([]).order_by, ("i", "alpha"))

    def test_ordering(self):
        # fallback to Table.Meta
        self.assertEqual(OrderedTable([], order_by=None).order_by, ("alpha",))
        self.assertEqual(OrderedTable([]).order_by, ("alpha",))

        # values of order_by are wrapped in tuples before being returned
        self.assertEqual(OrderedTable([], order_by="alpha").order_by, ("alpha",))
        self.assertEqual(OrderedTable([], order_by=("beta",)).order_by, ("beta",))

        for test in [[], (), ""]:
            table = OrderedTable([])
            table.order_by = test
            self.assertEqual(table.order_by, ())
            self.assertEqual(table.order_by, OrderedTable([], order_by=[]).order_by)

        # apply an ordering
        table = UnorderedTable([])
        table.order_by = "alpha"
        self.assertEqual(table.order_by, ("alpha",))
        self.assertEqual(UnorderedTable([], order_by="alpha").order_by, ("alpha",))

        # let's check the data
        table = OrderedTable(MEMORY_DATA, order_by="beta")
        self.assertEqual(table.rows[0].get_cell("i"), 3)

        table = OrderedTable(MEMORY_DATA, order_by="-beta")
        self.assertEqual(table.rows[0].get_cell("i"), 1)

        # allow fallback to Table.Meta.order_by
        table = OrderedTable(MEMORY_DATA)
        self.assertEqual(table.rows[0].get_cell("i"), 1)

        # column's can't be ordered if they're not allowed to be
        class TestTable2(tables.Table):
            a = tables.Column(orderable=False)
            b = tables.Column()

        table = TestTable2([], order_by="a")
        self.assertEqual(table.order_by, ())

        table = TestTable2([], order_by="b")
        self.assertEqual(table.order_by, ("b",))

        # ordering disabled by default
        class TestTable3(tables.Table):
            a = tables.Column(orderable=True)
            b = tables.Column()

            class Meta:
                orderable = False

        table = TestTable3([], order_by="a")
        self.assertEqual(table.order_by, ("a",))

        table = TestTable3([], order_by="b")
        self.assertEqual(table.order_by, ())

        table = TestTable3([], orderable=True, order_by="b")
        self.assertEqual(table.order_by, ("b",))

    def test_ordering_different_types(self):
        data = [
            {"i": 1, "alpha": datetime.now(), "beta": [1]},
            {"i": {}, "alpha": None, "beta": ""},
            {"i": 2, "alpha": None, "beta": []},
        ]

        table = OrderedTable(data)
        self.assertEqual(table.rows[0].get_cell("alpha"), "—")

        table = OrderedTable(data, order_by="i")
        self.assertEqual(table.rows[0].get_cell("i"), {})

        table = OrderedTable(data, order_by="beta")
        self.assertEqual(table.rows[0].get_cell("beta"), [])

    def test_multi_column_ordering_by_table(self):
        class PersonTable(tables.Table):
            first_name = tables.Column()
            last_name = tables.Column()

        brad, brad2, chris, davina, ross = PEOPLE

        table = PersonTable(PEOPLE, order_by=("first_name", "last_name"))
        self.assertEqual([brad, brad2, chris, davina, ross], [r.record for r in table.rows])

        table = PersonTable(PEOPLE, order_by=("first_name", "-last_name"))
        self.assertEqual([brad2, brad, chris, davina, ross], [r.record for r in table.rows])

    def test_multi_column_ordering_by_column(self):
        # let's try column order_by using multiple keys
        class PersonTable(tables.Table):
            name = tables.Column(order_by=("first_name", "last_name"))

        brad, brad2, chris, davina, ross = PEOPLE

        # add 'name' key for each person.
        for person in PEOPLE:
            person["name"] = f"{person['first_name']} {person['last_name']}"
        self.assertEqual(brad["name"], "Bradley Ayers")

        table = PersonTable(PEOPLE, order_by="name")
        self.assertEqual([brad, brad2, chris, davina, ross], [r.record for r in table.rows])

        table = PersonTable(PEOPLE, order_by="-name")
        self.assertEqual([ross, davina, chris, brad2, brad], [r.record for r in table.rows])

    def test_ordering_by_custom_field(self):
        """
        When defining a custom field in a table, as name=tables.Column() with
        methods to render and order render_name and order_name, sorting by this
        column causes an error if the custom field is not in last position.
        https://github.com/jieter/django-tables2/issues/413
        """

        Person.objects.create(first_name="Alice", last_name="Beta")
        Person.objects.create(first_name="Bob", last_name="Alpha")

        from django.db.models import F, Value
        from django.db.models.functions import Concat

        class PersonTable(tables.Table):
            first_name = tables.Column()
            last_name = tables.Column()
            full_name = tables.Column()

            class Meta:
                model = Person
                fields = ("first_name", "last_name", "full_name")

            def render_full_name(self, record):
                return record.last_name + " " + record.first_name

            def order_full_name(self, queryset, is_descending):
                queryset = queryset.annotate(
                    full_name=Concat(F("last_name"), Value(" "), F("first_name"))
                ).order_by(("-" if is_descending else "") + "full_name")
                return queryset, True

        table = PersonTable(Person.objects.all())
        request = build_request("/?sort=full_name&sort=first_name")
        RequestConfig(request).configure(table)

        self.assertEqual(table.rows[0].record.first_name, "Bob")

    def test_list_table_data_supports_ordering(self):
        class Table(tables.Table):
            name = tables.Column()

        data = [{"name": "Bradley"}, {"name": "Davina"}]

        table = Table(data)
        self.assertEqual(table.rows[0].get_cell("name"), "Bradley")
        table.order_by = "-name"
        self.assertEqual(table.rows[0].get_cell("name"), "Davina")

    def test_ordering_non_database_data(self):
        class Table(tables.Table):
            name = tables.Column()
            country = tables.Column()

        data = [
            {"name": "Adrian", "country": "Australia"},
            {"name": "Adrian", "country": "Brazil"},
            {"name": "Audrey", "country": "Chile"},
            {"name": "Bassie", "country": "Belgium"},
        ]
        table = Table(data, order_by=("-name", "-country"))

        self.assertEqual(
            [(row.get_cell("name"), row.get_cell("country")) for row in table.rows],
            [
                ("Bassie", "Belgium"),
                ("Audrey", "Chile"),
                ("Adrian", "Brazil"),
                ("Adrian", "Australia"),
            ],
        )

    def test_table_ordering_attributes(self):
        class Table(tables.Table):
            alpha = tables.Column()
            beta = tables.Column()

        table = Table(
            MEMORY_DATA,
            attrs={
                "th": {
                    "class": "custom-header-class",
                    "_ordering": {
                        "orderable": "sortable",
                        "ascending": "ascend",
                        "descending": "descend",
                    },
                }
            },
            order_by="alpha",
        )

        self.assertIn("sortable", table.columns[0].attrs["th"]["class"])
        self.assertIn("ascend", table.columns[0].attrs["th"]["class"])
        self.assertIn("custom-header-class", table.columns[1].attrs["th"]["class"])

    def test_table_ordering_attributes_in_meta(self):
        class Table(tables.Table):
            alpha = tables.Column()
            beta = tables.Column()

            class Meta(OrderedTable.Meta):
                attrs = {
                    "th": {
                        "class": "custom-header-class-in-meta",
                        "_ordering": {
                            "orderable": "sortable",
                            "ascending": "ascend",
                            "descending": "descend",
                        },
                    }
                }

        table = Table(MEMORY_DATA)

        self.assertIn("sortable", table.columns[0].attrs["th"]["class"])
        self.assertIn("ascend", table.columns[0].attrs["th"]["class"])
        self.assertIn("custom-header-class-in-meta", table.columns[1].attrs["th"]["class"])

    def test_column_ordering_attributes(self):
        class Table(tables.Table):
            alpha = tables.Column(
                attrs={
                    "th": {
                        "class": "custom-header-class",
                        "_ordering": {"orderable": "sort", "ascending": "ascending"},
                    }
                }
            )
            beta = tables.Column(
                attrs={"th": {"_ordering": {"orderable": "canOrder"}}, "td": {"class": "cell-2"}}
            )

        table = Table(MEMORY_DATA, attrs={"class": "only-on-table"}, order_by="alpha")

        self.assertNotIn("only-on-table", table.columns[0].attrs["th"]["class"])
        self.assertIn("custom-header-class", table.columns[0].attrs["th"]["class"])
        self.assertIn("ascending", table.columns[0].attrs["th"]["class"])
        self.assertIn("sort", table.columns[0].attrs["th"]["class"])
        self.assertIn("canOrder", table.columns[1].attrs["th"]["class"])
