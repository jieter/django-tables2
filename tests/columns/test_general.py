from django.core.exceptions import ImproperlyConfigured
from django.db import models
from django.test import TestCase
from django.utils.safestring import SafeData, mark_safe
from django.utils.translation import gettext_lazy

import django_tables2 as tables

from ..app.models import Person
from ..utils import build_request, parse

request = build_request("/")


class ColumnGeneralTest(TestCase):
    def test_column_render_supports_kwargs(self):
        class TestColumn(tables.Column):
            def render(self, **kwargs):
                return set(kwargs.keys())

        class TestTable(tables.Table):
            foo = TestColumn()

        table = TestTable([{"foo": "bar"}])
        expected = {"record", "value", "column", "bound_column", "bound_row", "table"}
        self.assertEqual(table.rows[0].get_cell("foo"), expected)

    def test_column_header_should_use_titlised_verbose_name_unless_given_explicitly(self):
        class SimpleTable(tables.Table):
            basic = tables.Column()
            acronym = tables.Column(verbose_name="has FBI help")

        table = SimpleTable([])
        self.assertEqual(table.columns["basic"].header, "Basic")
        self.assertEqual(table.columns["acronym"].header, "has FBI help")

    def test_should_support_safe_verbose_name(self):
        class SimpleTable(tables.Table):
            safe = tables.Column(verbose_name=mark_safe("<b>Safe</b>"))

        table = SimpleTable([])
        self.assertIsInstance(table.columns["safe"].header, SafeData)

    def test_should_raise_on_invalid_accessor(self):
        with self.assertRaises(TypeError):

            class SimpleTable(tables.Table):
                column = tables.Column(accessor={})

    def test_column_with_callable_accessor_should_not_have_default(self):
        with self.assertRaises(TypeError):

            class SimpleTable(tables.Table):
                column = tables.Column(accessor=lambda: "foo", default="")

    def test_should_support_safe_verbose_name_via_model(self):
        class PersonTable(tables.Table):
            safe = tables.Column()

        table = PersonTable(Person.objects.all())
        self.assertIsInstance(table.columns["safe"].header, SafeData)

    def test_should_support_empty_string_as_explicit_verbose_name(self):
        class SimpleTable(tables.Table):
            acronym = tables.Column(verbose_name="")

        table = SimpleTable([])
        self.assertEqual(table.columns["acronym"].header, "")

    def test_handle_verbose_name_of_many2onerel(self):
        class Table(tables.Table):
            count = tables.Column(accessor="info_list.count")

        Person.objects.create(first_name="bradley", last_name="ayers")
        table = Table(Person.objects.all())
        self.assertEqual(table.columns["count"].verbose_name, "Information")

    def test_orderable(self):
        class SimpleTable(tables.Table):
            name = tables.Column()

        table = SimpleTable([])
        self.assertTrue(table.columns["name"].orderable)

        class SimpleTable(tables.Table):
            name = tables.Column()

            class Meta:
                orderable = False

        table = SimpleTable([])
        self.assertFalse(table.columns["name"].orderable)

        class SimpleTable(tables.Table):
            name = tables.Column()

            class Meta:
                orderable = True

        table = SimpleTable([])
        self.assertTrue(table.columns["name"].orderable)

    def test_order_by_defaults_to_accessor(self):
        class SimpleTable(tables.Table):
            foo = tables.Column(accessor="bar")

        table = SimpleTable([])
        self.assertEqual(table.columns["foo"].order_by, ("bar",))

    def test_supports_order_by(self):
        class SimpleTable(tables.Table):
            name = tables.Column(order_by=("last_name", "-first_name"))
            age = tables.Column()

        table = SimpleTable([], order_by=("-age",))
        # alias
        self.assertEqual(table.columns["name"].order_by_alias, "name")
        self.assertEqual(table.columns["age"].order_by_alias, "-age")
        # order by
        self.assertEqual(table.columns["name"].order_by, ("last_name", "-first_name"))
        self.assertEqual(table.columns["age"].order_by, ("-age",))

        # now try with name ordered
        table = SimpleTable([], order_by=("-name",))
        # alias
        self.assertEqual(table.columns["name"].order_by_alias, "-name")
        self.assertEqual(table.columns["age"].order_by_alias, "age")
        # alias next
        self.assertEqual(table.columns["name"].order_by_alias.next, "name")
        self.assertEqual(table.columns["age"].order_by_alias.next, "age")
        # order by
        self.assertEqual(table.columns["name"].order_by, ("-last_name", "first_name"))
        self.assertEqual(table.columns["age"].order_by, ("age",))

    def test_supports_is_ordered(self):
        class SimpleTable(tables.Table):
            name = tables.Column()

        # sorted
        table = SimpleTable([], order_by="name")
        self.assertTrue(table.columns["name"].is_ordered)
        # unsorted
        table = SimpleTable([])
        self.assertFalse(table.columns["name"].is_ordered)

    def test_translation(self):
        """
        Tests different types of values for the ``verbose_name`` property of a
        column.
        """

        class TranslationTable(tables.Table):
            text = tables.Column(verbose_name=gettext_lazy("Text"))

        table = TranslationTable([])
        self.assertEqual(table.columns["text"].header, "Text")

    def test_sequence(self):
        """
        Ensures that the sequence of columns is configurable.
        """

        class TestTable(tables.Table):
            a = tables.Column()
            b = tables.Column()
            c = tables.Column()

        self.assertEqual(["a", "b", "c"], TestTable([]).columns.names())
        self.assertEqual(["b", "a", "c"], TestTable([], sequence=("b", "a", "c")).columns.names())

        class TestTable2(TestTable):
            class Meta:
                sequence = ("b", "a", "c")

        self.assertEqual(["b", "a", "c"], TestTable2([]).columns.names())
        self.assertEqual(["a", "b", "c"], TestTable2([], sequence=("a", "b", "c")).columns.names())

        class TestTable3(TestTable):
            class Meta:
                sequence = ("c",)

        self.assertEqual(["c", "a", "b"], TestTable3([]).columns.names())
        self.assertEqual(["c", "a", "b"], TestTable([], sequence=("c",)).columns.names())

        class TestTable4(TestTable):
            class Meta:
                sequence = ("...",)

        self.assertEqual(["a", "b", "c"], TestTable4([]).columns.names())
        self.assertEqual(["a", "b", "c"], TestTable([], sequence=("...",)).columns.names())

        class TestTable5(TestTable):
            class Meta:
                sequence = ("b", "...")

        self.assertEqual(["b", "a", "c"], TestTable5([]).columns.names())
        self.assertEqual(["b", "a", "c"], TestTable([], sequence=("b", "...")).columns.names())

        class TestTable6(TestTable):
            class Meta:
                sequence = ("...", "b")

        self.assertEqual(["a", "c", "b"], TestTable6([]).columns.names())
        self.assertEqual(["a", "c", "b"], TestTable([], sequence=("...", "b")).columns.names())

        class TestTable7(TestTable):
            class Meta:
                sequence = ("b", "...", "a")

        self.assertEqual(["b", "c", "a"], TestTable7([]).columns.names())
        self.assertEqual(["b", "c", "a"], TestTable([], sequence=("b", "...", "a")).columns.names())

        # Let's test inheritence
        class TestTable8(TestTable):
            d = tables.Column()
            e = tables.Column()
            f = tables.Column()

            class Meta:
                sequence = ("d", "...")

        class TestTable9(TestTable):
            d = tables.Column()
            e = tables.Column()
            f = tables.Column()

        self.assertEqual(["d", "a", "b", "c", "e", "f"], TestTable8([]).columns.names())
        self.assertEqual(
            ["d", "a", "b", "c", "e", "f"], TestTable9([], sequence=("d", "...")).columns.names()
        )

    def test_should_support_both_meta_sequence_and_constructor_exclude(self):
        """
        Issue #32 describes a problem when both ``Meta.sequence`` and
        ``Table(..., exclude=...)`` are used on a single table. The bug caused an
        exception to be raised when the table was iterated.
        """

        class SequencedTable(tables.Table):
            a = tables.Column()
            b = tables.Column()
            c = tables.Column()

            class Meta:
                sequence = ("a", "...")

        table = SequencedTable([], exclude=("c",))
        table.as_html(request)
        self.assertEqual(table.columns.names(), ["a", "b"])

    def test_bound_columns_should_support_indexing(self):
        class SimpleTable(tables.Table):
            a = tables.Column()
            b = tables.Column()

        table = SimpleTable([])
        self.assertEqual(table.columns[1].name, "b")
        self.assertEqual(table.columns["b"].name, "b")

    def test_cell_attrs_applies_to_td_and_th_and_footer_td(self):
        class SimpleTable(tables.Table):
            a = tables.Column(
                attrs={"cell": {"key": "value"}}, footer=lambda table: len(table.data)
            )

        # providing data ensures 1 row is rendered
        table = SimpleTable([{"a": "value"}])
        root = parse(table.as_html(request))

        self.assertEqual(
            root.findall(".//thead/tr/th")[0].attrib, {"key": "value", "class": "orderable"}
        )
        self.assertEqual(root.findall(".//tbody/tr/td")[0].attrib, {"key": "value"})
        self.assertEqual(root.findall(".//tfoot/tr/td")[0].attrib, {"key": "value"})

    def test_th_are_given_orderable_class_if_column_is_orderable(self):
        class SimpleTable(tables.Table):
            a = tables.Column()
            b = tables.Column(orderable=False)

        table = SimpleTable([{"a": "value"}])
        root = parse(table.as_html(request))
        # return classes of an element as a set
        classes = lambda x: set(x.attrib.get("class", "").split())
        self.assertIn("orderable", classes(root.findall(".//thead/tr/th")[0]))
        self.assertNotIn("orderable", classes(root.findall(".//thead/tr/th")[1]))

        # Now try with an ordered table
        table = SimpleTable([], order_by="a")
        root = parse(table.as_html(request))
        # return classes of an element as a set
        self.assertIn("orderable", classes(root.findall(".//thead/tr/th")[0]))
        self.assertIn("asc", classes(root.findall(".//thead/tr/th")[0]))
        self.assertNotIn("orderable", classes(root.findall(".//thead/tr/th")[1]))

    def test_empty_values_triggers_default(self):
        class Table(tables.Table):
            a = tables.Column(empty_values=(1, 2), default="--")

        table = Table([{"a": 1}, {"a": 2}, {"a": 3}, {"a": 4}])
        self.assertEqual([row.get_cell("a") for row in table.rows], ["--", "--", 3, 4])

    def test_register_skips_non_columns(self):
        from django_tables2.columns.base import library

        currently_registered = len(library.columns)

        with self.assertRaises(ImproperlyConfigured):

            @library.register
            class Klass(object):
                pass

        self.assertEqual(len(library.columns), currently_registered)

    def test_raises_when_using_non_supported_index(self):
        class Table(tables.Table):
            column = tables.Column()

        table = Table([{"column": "foo"}])

        row = table.rows[0]
        with self.assertRaises(TypeError):
            row[table]

    def test_related_fields_get_correct_type(self):
        """
        Types of related fields should also lead to the correct type of column.
        """

        class PersonTable(tables.Table):
            class Meta:
                model = Person
                fields = ["first_name", "occupation.boolean"]

        table = PersonTable([])
        self.assertEqual(
            [type(column).__name__ for column in table.base_columns.values()],
            ["Column", "BooleanColumn"],
        )


class MyModel(models.Model):
    item1 = models.CharField(max_length=10)

    class Meta:
        app_label = "django_tables2_tests"


class MyTable(tables.Table):
    item1 = tables.Column(verbose_name="Nice column name")

    class Meta:
        model = MyModel
        fields = ("item1",)


class ColumnInheritanceTest(TestCase):
    def test_column_params_should_be_preserved_under_inheritance(self):
        """
        Github issue #337

        Columns explicitly defined on MyTable get overridden by columns implicitly
        defined on it's child.
        If the column is not redefined, the explicit definition of MyTable is used,
        preserving the specialized verbose_name defined on it.
        """

        class MyTableA(MyTable):
            """
            having an empty `class Meta` should not undo the explicit definition
            of column item1 in MyTable.
            """

            class Meta(MyTable.Meta):
                pass

        class MyTableB(MyTable):
            """
            having a non-empty `class Meta` should not undo the explicit definition
            of column item1 in MyTable.
            """

            class Meta(MyTable.Meta):
                per_page = 22

        table = MyTable(MyModel.objects.all())
        tableA = MyTableA(MyModel.objects.all())
        tableB = MyTableB(MyModel.objects.all())

        self.assertEqual(table.columns["item1"].verbose_name, "Nice column name")
        self.assertEqual(tableA.columns["item1"].verbose_name, "Nice column name")
        self.assertEqual(tableB.columns["item1"].verbose_name, "Nice column name")

    def test_explicit_column_can_be_overridden_by_other_explicit_column(self):
        class MyTableC(MyTable):
            """
            If we define a new explict item1 column, that one should be used.
            """

            item1 = tables.Column(verbose_name="New nice column name")

        table = MyTable(MyModel.objects.all())
        tableC = MyTableC(MyModel.objects.all())

        self.assertEqual(table.columns["item1"].verbose_name, "Nice column name")
        self.assertEqual(tableC.columns["item1"].verbose_name, "New nice column name")

    def test_override_column_class_names(self):
        """
        We control the output of CSS class names for a column by overriding
        get_column_class_names
        """

        class MyTable(tables.Table):
            population = tables.Column(verbose_name="Population")

            def get_column_class_names(self, classes_set, bound_column):
                classes_set.add("prefix-%s" % bound_column.name)
                return classes_set

        TEST_DATA = [
            {"name": "Belgium", "population": 11200000},
            {"name": "Luxembourgh", "population": 540000},
            {"name": "France", "population": 66000000},
        ]

        html = MyTable(TEST_DATA).as_html(build_request())

        self.assertIn('<td class="prefix-population">11200000</td>', html)


class ColumnAttrsTest(TestCase):
    def setUp(self):
        Person.objects.create(first_name="Jan", last_name="Pietersz.")
        Person.objects.create(first_name="Sjon", last_name="Jansen")

    def test_computable_td_attrs(self):
        """Computable attrs for columns, using table argument"""

        class Table(tables.Table):
            person = tables.Column(attrs={"cell": {"data-length": lambda table: len(table.data)}})
            first_name = tables.Column(
                attrs={"td": {"class": lambda table: "status-{}".format(len(table.data))}}
            )

        table = Table(Person.objects.all())
        html = table.as_html(request)
        # cell should affect both <th> and <td>
        self.assertIn('<th data-length="2" class="orderable">', html)
        self.assertIn('<td data-length="2">', html)
        # td should only affect <td>
        self.assertIn('<td class="status-2">', html)

    def test_computable_td_attrs_defined_in_column_class_attribute(self):
        """Computable attrs for columns, using custom Column"""

        class MyColumn(tables.Column):
            attrs = {"td": {"data-test": lambda table: len(table.data)}}

        class Table(tables.Table):
            last_name = MyColumn()

        table = Table(Person.objects.all())
        html = table.as_html(request)
        root = parse(html)

        self.assertEqual(root.findall(".//tbody/tr/td")[0].attrib, {"data-test": "2"})
        self.assertEqual(root.findall(".//tbody/tr/td")[1].attrib, {"data-test": "2"})

    def test_computable_td_attrs_defined_in_column_class_attribute_record(self):
        """Computable attrs for columns, using custom column"""

        class PersonColumn(tables.Column):
            attrs = {
                "td": {
                    "data-first-name": lambda record: record.first_name,
                    "data-last-name": lambda record: record.last_name,
                }
            }

            def render(self, record):
                return "{} {}".format(record.first_name, record.last_name)

        class Table(tables.Table):
            person = PersonColumn(empty_values=())

        table = Table(Person.objects.all())
        html = table.as_html(request)
        root = parse(html)

        self.assertEqual(
            root.findall(".//tbody/tr/td")[0].attrib,
            {"data-first-name": "Jan", "data-last-name": "Pietersz."},
        )

    def test_computable_column_td_attrs_record_header(self):
        """
        Computable attrs for columns, using custom column with a callable containing
        a catch-all argument.
        """

        def data_first_name(**kwargs):
            record = kwargs.get("record", None)
            return "header" if not record else record.first_name

        class Table(tables.Table):
            first_name = tables.Column(
                attrs={
                    "cell": {
                        "data-first-name": data_first_name,
                        "class": lambda value: "status-{}".format(value),
                    }
                }
            )

        table = Table(Person.objects.all())
        html = table.as_html(request)
        root = parse(html)

        self.assertEqual(
            root.findall(".//thead/tr/th")[0].attrib,
            {"class": "orderable", "data-first-name": "header"},
        )
        self.assertEqual(
            root.findall(".//tbody/tr/td")[0].attrib,
            {"class": "status-Jan", "data-first-name": "Jan"},
        )
        self.assertEqual(
            root.findall(".//tbody/tr/td")[1].attrib,
            {"class": "status-Sjon", "data-first-name": "Sjon"},
        )
