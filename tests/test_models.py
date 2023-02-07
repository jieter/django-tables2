from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models.functions import Length
from django.template import Context, Template
from django.test import TestCase
from django.utils.translation import override as translation_override
from unittest import mock

import django_tables2 as tables

from .app.models import Occupation, Person, PersonProxy, Region
from .utils import build_request, parse

request = build_request()


class PersonTable(tables.Table):
    first_name = tables.Column()
    last_name = tables.Column()
    occupation = tables.Column()


class ModelsTest(TestCase):
    def setUp(self):
        occupation = Occupation.objects.create(name="Programmer", boolean=True)
        Person.objects.create(first_name="Bradley", last_name="Ayers", occupation=occupation)
        Person.objects.create(first_name="Chris", last_name="Doble", occupation=occupation)

    def test_check_types_model(self):
        class Abstract(models.Model):
            name = models.CharField(max_length=100)

            class Meta:
                abstract = True
                app_label = "django_tables2_test"

        class Concrete(Abstract):
            pass

        def test(Model):
            class Table(tables.Table):
                class Meta:
                    model = Model

            return Table([])

        valid = [
            Abstract,
            Concrete,
            Occupation,
            Person,
            PersonProxy,
            ContentType.objects.get(model="person").model_class(),
        ]
        for Model in valid:
            test(Model)

        for Model in [object, {}, dict]:
            with self.assertRaises(TypeError):
                test(Model)

    def test_boundrows_iteration(self):
        table = PersonTable(Person.objects.all())
        expected = list(Person.objects.all())
        for i, actual in enumerate([row.record for row in table.rows]):
            self.assertEqual(expected[i], actual)

    def test_should_support_rendering_multiple_times(self):
        class MultiRenderTable(tables.Table):
            name = tables.Column()

        # test queryset data
        table = MultiRenderTable(Person.objects.all())
        self.assertEqual(table.as_html(request), table.as_html(request))

    def test_doesnotexist_from_accessor_should_use_default(self):
        class Table(tables.Table):
            class Meta:
                model = Person
                default = "abc"
                fields = ("first_name", "last_name", "region")

        table = Table(Person.objects.all())
        self.assertEqual(table.rows[0].get_cell("first_name"), "Bradley")
        self.assertEqual(table.rows[0].get_cell("region"), "abc")

    def test_unicode_field_names(self):
        class Table(tables.Table):
            class Meta:
                model = Person
                fields = ("first_name",)

        table = Table(Person.objects.all())
        self.assertEqual(table.rows[0].get_cell("first_name"), "Bradley")

    def test_Meta_option_model_table(self):
        """
        The ``model`` option on a table causes the table to dynamically add columns
        based on the fields.
        """

        class OccupationTable(tables.Table):
            class Meta:
                model = Occupation

        expected = ["id", "name", "region", "boolean", "boolean_with_choices"]
        self.assertEqual(expected, list(OccupationTable.base_columns.keys()))

        class OccupationTable2(tables.Table):
            extra = tables.Column()

            class Meta:
                model = Occupation

        expected.append("extra")
        self.assertEqual(expected, list(OccupationTable2.base_columns.keys()))

        # be aware here, we already have *models* variable, but we're importing
        # over the top
        from django.db import models

        class ComplexModel(models.Model):
            char = models.CharField(max_length=200)
            fk = models.ForeignKey("self", on_delete=models.CASCADE)
            m2m = models.ManyToManyField("self")

            class Meta:
                app_label = "django_tables2_test"

        class ComplexTable(tables.Table):
            class Meta:
                model = ComplexModel

        self.assertEqual(["id", "char", "fk"], list(ComplexTable.base_columns.keys()))

    def test_mixins(self):
        class TableMixin(tables.Table):
            extra = tables.Column()

        class OccupationTable(TableMixin, tables.Table):
            extra2 = tables.Column()

            class Meta:
                model = Occupation

        self.assertEqual(
            list(OccupationTable.base_columns.keys()),
            ["extra", "id", "name", "region", "boolean", "boolean_with_choices", "extra2"],
        )

    def test_fields_empty_list_means_no_fields(self):
        class Table(tables.Table):
            class Meta:
                model = Person
                fields = ()

        table = Table(Person.objects.all())
        self.assertEqual(len(table.columns.names()), 0)

    def test_compound_ordering(self):
        class SimpleTable(tables.Table):
            name = tables.Column(order_by=("first_name", "last_name"))

        table = SimpleTable(Person.objects.all(), order_by="name")
        html = table.as_html(request)
        self.assertEqual(parse(html).findall(".//thead/tr/th/a")[0].attrib, {"href": "?sort=-name"})

    def test_default_order(self):
        """
        If orderable=False, do not sort queryset.
        https://github.com/bradleyayers/django-tables2/issues/204
        """

        class PersonTable(tables.Table):
            first_name = tables.Column()
            last_name = tables.Column()

        table = PersonTable(PersonProxy.objects.all())
        table.data.order_by([])
        self.assertEqual(list(table.rows[0]), ["Bradley", "Ayers"])

    def test_fields_should_implicitly_set_sequence(self):
        class PersonTable(tables.Table):
            extra = tables.Column()

            class Meta:
                model = Person
                fields = ("last_name", "first_name")

        table = PersonTable(Person.objects.all())
        self.assertEqual(table.columns.names(), ["last_name", "first_name", "extra"])

    def test_model_properties_should_be_useable_for_columns(self):
        class PersonTable(tables.Table):
            class Meta:
                model = Person
                fields = ("name", "first_name")

        table = PersonTable(Person.objects.all())
        self.assertEqual(list(table.rows[0]), ["Bradley Ayers", "Bradley"])

    def test_meta_fields_may_be_list(self):
        class PersonTable(tables.Table):
            class Meta:
                model = Person
                fields = ["name", "first_name"]

        table = PersonTable(Person.objects.all())
        self.assertEqual(list(table.rows[0]), ["Bradley Ayers", "Bradley"])

    def test_meta_fields_can_traverse_relations(self):
        mayor = Person.objects.create(first_name="Buddy", last_name="Boss")
        region = Region.objects.create(name="Zuid-Holland", mayor=mayor)
        occupation = Occupation.objects.create(name="carpenter", region=region)
        Person.objects.create(first_name="Bob", last_name="Builder", occupation=occupation)

        class PersonTable(tables.Table):
            class Meta:
                model = Person
                fields = [
                    "name",
                    "occupation__name",
                    "occupation__region__name",
                    "occupation__region__mayor__name",
                ]

        table = PersonTable(Person.objects.filter(occupation=occupation))
        self.assertEqual(
            list(table.rows[0]), ["Bob Builder", "carpenter", "Zuid-Holland", "Buddy Boss"]
        )

    def test_meta_linkify_iterable(self):
        person = Person.objects.first()

        class PersonTable(tables.Table):
            class Meta:
                model = Person
                fields = ["name", "occupation__boolean"]
                linkify = ["name", "occupation__boolean"]

        table = PersonTable(Person.objects.all())

        html = table.as_html(build_request())
        self.assertIn(f'<a href="/people/{person.pk}/">{person.name}</a>', html)
        self.assertIn(f'<a href="/people/{person.pk}/"><span class="true">✔</span></a>', html)

    def test_meta_linkify_dict(self):
        person = Person.objects.first()
        occupation = person.occupation

        class PersonTable(tables.Table):
            class Meta:
                model = Person
                fields = ["name", "occupation", "occupation__boolean"]
                linkify = {
                    "name": lambda record: record.get_absolute_url(),
                    "occupation": True,
                    "occupation__boolean": ("occupation", {"pk": tables.A("occupation__id")}),
                }

        table = PersonTable(Person.objects.all())

        html = table.as_html(build_request())
        self.assertIn(f'<a href="{person.get_absolute_url()}">{person.name}</a>', html)
        self.assertIn(f'<a href="{occupation.get_absolute_url()}">{occupation.name}</a>', html)

        self.assertIn(
            f'<a href="{occupation.get_absolute_url()}"><span class="true">✔</span></a>', html
        )


class ColumnNameTest(TestCase):
    def setUp(self):
        for i in range(10):
            Person.objects.create(first_name=f"Bob {i}", last_name="Builder")

    def test_column_verbose_name(self):
        """
        When using queryset data as input for a table, default to using model field
        verbose names rather than an autogenerated string based on the column name.

        However if a column does explicitly describe a verbose name, it should be
        used.
        """

        class PersonTable(tables.Table):
            """
            The test_colX columns are to test that the accessor is used to
            determine the field on the model, rather than the column name.
            """

            first_name = tables.Column()
            fn1 = tables.Column(accessor="first_name")
            fn2 = tables.Column(accessor="first_name__upper")
            fn3 = tables.Column(accessor="last_name", verbose_name="OVERRIDE")
            fn4 = tables.Column(accessor="last_name", verbose_name="override")
            last_name = tables.Column()
            ln1 = tables.Column(accessor="last_name")
            ln2 = tables.Column(accessor="last_name__upper")
            ln3 = tables.Column(accessor="last_name", verbose_name="OVERRIDE")
            region = tables.Column(accessor="occupation__region__name")
            r1 = tables.Column(accessor="occupation__region__name")
            r2 = tables.Column(accessor="occupation__region__name__upper")
            r3 = tables.Column(accessor="occupation__region__name", verbose_name="OVERRIDE")
            trans_test = tables.Column()
            trans_test_lazy = tables.Column()

        # The Person model has a ``first_name`` and ``last_name`` field, but only
        # the ``last_name`` field has an explicit ``verbose_name`` set. This means
        # that we should expect that the two columns that use the ``last_name``
        # field should both use the model's ``last_name`` field's ``verbose_name``,
        # however both fields that use the ``first_name`` field should just use a
        # titlised version of the column name as the column header.
        table = PersonTable(Person.objects.all())

        # Should be generated (capitalized column name)
        self.assertEqual("First name", table.columns["first_name"].verbose_name)
        self.assertEqual("First name", table.columns["fn1"].verbose_name)
        self.assertEqual("First name", table.columns["fn2"].verbose_name)
        self.assertEqual("OVERRIDE", table.columns["fn3"].verbose_name)
        self.assertEqual("override", table.columns["fn4"].verbose_name)
        # Should use the titlised model field's verbose_name
        self.assertEqual("Surname", table.columns["last_name"].verbose_name)
        self.assertEqual("Surname", table.columns["ln1"].verbose_name)
        self.assertEqual("Surname", table.columns["ln2"].verbose_name)
        self.assertEqual("OVERRIDE", table.columns["ln3"].verbose_name)
        self.assertEqual("Name", table.columns["region"].verbose_name)
        self.assertEqual("Name", table.columns["r1"].verbose_name)
        self.assertEqual("Name", table.columns["r2"].verbose_name)
        self.assertEqual("OVERRIDE", table.columns["r3"].verbose_name)
        self.assertEqual("Translation test", table.columns["trans_test"].verbose_name)
        self.assertEqual("Translation test lazy", table.columns["trans_test_lazy"].verbose_name)

    def test_using_Meta_model(self):
        # Now we'll try using a table with Meta.model
        class PersonTable(tables.Table):
            first_name = tables.Column(verbose_name="OVERRIDE")

            class Meta:
                model = Person

        # Issue #16
        table = PersonTable(Person.objects.all())
        self.assertEqual("Translation test", table.columns["trans_test"].verbose_name)
        self.assertEqual("Translation test lazy", table.columns["trans_test_lazy"].verbose_name)
        self.assertEqual("Web site", table.columns["website"].verbose_name)
        self.assertEqual("Birthdate", table.columns["birthdate"].verbose_name)
        self.assertEqual("OVERRIDE", table.columns["first_name"].verbose_name)

        class PersonTable(tables.Table):
            class Meta:
                model = Person

        table = PersonTable(Person.objects.all())
        with translation_override("ua"):
            self.assertEqual(
                "Тест ленивого перекладу", table.columns["trans_test_lazy"].verbose_name
            )

    def test_data_verbose_name(self):
        table = tables.Table(Person.objects.all())
        self.assertEqual(table.data.verbose_name, "person")
        self.assertEqual(table.data.verbose_name_plural, "people")

    def test_column_named_delete(self):
        class DeleteTable(tables.Table):
            delete = tables.TemplateColumn("[delete button]", verbose_name="")

            class Meta:
                model = Person
                fields = ("name", "delete")

        person1 = Person.objects.create(first_name="Jan", last_name="Pieter")
        person2 = Person.objects.create(first_name="John", last_name="Peter")

        DeleteTable(Person.objects.all()).as_html(build_request())

        self.assertEqual(Person.objects.get(pk=person1.pk), person1)
        self.assertEqual(Person.objects.get(pk=person2.pk), person2)


class ModelFieldTest(TestCase):
    def test_use_to_translated_value(self):
        """
        When a model field uses the ``choices`` option, a table should render the
        'pretty' value rather than the database value.

        See issue #30 for details.
        """
        LANGUAGES = (("en", "English"), ("ru", "Russian"))

        from django.db import models

        class Article(models.Model):
            name = models.CharField(max_length=200)
            language = models.CharField(max_length=200, choices=LANGUAGES)

            class Meta:
                app_label = "tests"

            def __unicode__(self):
                return self.name

        class ArticleTable(tables.Table):
            class Meta:
                model = Article

        table = ArticleTable(
            [
                Article(name="English article", language="en"),
                Article(name="Russian article", language="ru"),
            ]
        )

        self.assertEqual("English", table.rows[0].get_cell("language"))
        self.assertEqual("Russian", table.rows[1].get_cell("language"))

    def test_column_mapped_to_nonexistant_field(self):
        """
        Issue #9 describes how if a Table has a column that has an accessor that
        targets a non-existent field, a FieldDoesNotExist error is raised.
        """

        class FaultyPersonTable(PersonTable):
            missing = tables.Column()

        table = FaultyPersonTable(Person.objects.all())
        table.as_html(request)  # the bug would cause this to raise FieldDoesNotExist


class OrderingDataTest(TestCase):
    NAMES = ("Bradley Ayers", "Stevie Armstrong", "VeryLongFirstName VeryLongLastName")

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        for name in cls.NAMES:
            first_name, last_name = name.split()
            Person.objects.create(first_name=first_name, last_name=last_name)

    def test_order_by_derived_from_queryset(self):
        queryset = Person.objects.order_by("first_name", "last_name", "-occupation__name")

        class PersonTable(tables.Table):
            name = tables.Column(order_by=("first_name", "last_name"))
            occupation = tables.Column(order_by=("occupation__name",))

        self.assertEqual(
            PersonTable(queryset.order_by("first_name", "last_name", "-occupation__name")).order_by,
            ("name", "-occupation"),
        )

        class PersonTable(PersonTable):
            class Meta:
                order_by = ("occupation",)

        self.assertEqual(PersonTable(queryset.all()).order_by, ("occupation",))

    def test_queryset_table_data_supports_ordering(self):
        class Table(tables.Table):
            class Meta:
                model = Person

        table = Table(Person.objects.all())
        self.assertEqual(table.rows[0].get_cell("first_name"), "Bradley")
        table.order_by = "-first_name"
        self.assertEqual(table.rows[0].get_cell("first_name"), "VeryLongFirstName")

    def test_queryset_table_data_supports_custom_ordering(self):
        class Table(tables.Table):
            class Meta:
                model = Person
                order_by = "first_name"

            def order_first_name(self, queryset, is_descending):
                # annotate to order by length of first_name + last_name
                queryset = queryset.annotate(
                    length=Length("first_name") + Length("last_name")
                ).order_by(("-" if is_descending else "") + "length")
                return (queryset, True)

        table = Table(Person.objects.all())

        # Shortest full names first
        self.assertEqual(table.rows[0].get_cell("first_name"), "Bradley")

        # Longest full names first
        table.order_by = "-first_name"
        self.assertEqual(table.rows[0].get_cell("first_name"), "VeryLongFirstName")


class ModelSanityTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for i in range(10):
            Person.objects.create(first_name=f"Bob {i}", last_name="Builder")

    def test_column_with_delete_accessor_shouldnt_delete_records(self):
        class PersonTable(tables.Table):
            delete = tables.Column()

        table = PersonTable(Person.objects.all())
        table.as_html(request)

        self.assertEqual(Person.objects.all().count(), 10)

    def test_model__str__calls(self):
        """
        Model.__str__ should not be called when not necessary.
        """
        calls = defaultdict(int)

        def counting__str__(self):
            calls[self.pk] += 1
            return self.first_name

        with mock.patch("tests.app.models.Person.__str__", counting__str__):
            for i in range(1, 4):
                Person.objects.create(first_name=f"Bob {i}", last_name="Builder")

        class PersonTable(tables.Table):
            edit = tables.Column()

            class Meta:
                model = Person
                fields = ["first_name", "last_name"]

        self.assertEqual(calls, {})

        table = PersonTable(Person.objects.all())
        table.as_html(build_request())

        self.assertEqual(calls, {})

    def test_render_table_template_tag_numqueries(self):
        class PersonTable(tables.Table):
            class Meta:
                model = Person
                per_page = 1

        request = build_request("/")

        with self.assertNumQueries(0):
            table = PersonTable(Person.objects.all())

        with self.assertNumQueries(1):
            # one query for pagination: .count()
            tables.RequestConfig(request).configure(table)

        template = Template("{% load django_tables2 %}{% render_table table %}")
        context = Context({"table": table, "request": request})

        with self.assertNumQueries(1):
            # one query for page records
            template.render(context)

        with self.assertNumQueries(0):
            # re-render should not produce extra queries
            template.render(context)

        # second page
        request = build_request("/?page=2")
        context = Context({"table": table, "request": request})

        with self.assertNumQueries(0):
            # count is already done, not needed anymore
            tables.RequestConfig(request).configure(table)

        with self.assertNumQueries(1):
            # one query for page records
            template.render(context)

    def test_single_query_for_non_paginated_table(self):
        """
        A non-paginated table should not generate a query for each row, but only
        one query fetch the rows.
        """

        class PersonTable(tables.Table):
            class Meta:
                model = Person
                fields = ("first_name", "last_name")
                order_by = ("last_name", "first_name")

        table = PersonTable(Person.objects.all())

        with self.assertNumQueries(1):
            list(table.as_values())

    def test_as_html_db_queries_nonpaginated(self):
        """
        Basic tables without pagination should NOT result in a COUNT(*) being done,
        but only fetch the rows.
        """

        class PersonTable(tables.Table):
            class Meta:
                model = Person

        with self.assertNumQueries(1):
            html = PersonTable(Person.objects.all()).as_html(build_request())
            self.assertIn("Bob 0", html)


class TableFactoryTest(TestCase):
    def test_factory(self):
        occupation = Occupation.objects.create(name="Programmer")
        Person.objects.create(first_name="Bradley", last_name="Ayers", occupation=occupation)
        persons = Person.objects.all()
        Table = tables.table_factory(Person)
        table = Table(persons)
        self.assertIsInstance(table, tables.Table)
        self.assertEqual(Table.__name__, "PersonAutogeneratedTable")

    def test_factory_fields_argument(self):
        fields = ("username",)
        Table = tables.table_factory(Person, fields=fields)
        self.assertEqual(Table.Meta.fields, fields)
        self.assertEqual(Table._meta.fields, fields)

    def test_factory_exclude_argument(self):
        exclude = ("username",)
        Table = tables.table_factory(Person, exclude=exclude)
        self.assertEqual(Table.Meta.exclude, exclude)
        self.assertEqual(Table._meta.exclude, exclude)

    def test_factory_localize_argument(self):
        localize = ("username",)
        Table = tables.table_factory(Person, localize=localize)
        self.assertEqual(Table.Meta.localize, localize)
        self.assertEqual(Table._meta.localize, localize)

    def test_factory_with_meta(self):
        fields = ("first_name",)

        class TableWithMeta(tables.Table):
            first_name = tables.Column()

            class Meta:
                fields = ("first_name",)

        Table = tables.table_factory(Person, table=TableWithMeta)
        self.assertEqual(Table.Meta.fields, fields)
