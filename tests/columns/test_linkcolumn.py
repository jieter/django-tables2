from django.template import Context, Template
from django.test import TestCase
from django.urls import reverse
from django.utils.html import mark_safe

import django_tables2 as tables
from django_tables2 import A

from ..app.models import Occupation, Person
from ..utils import attrs, build_request


class LinkColumnTest(TestCase):
    def test_unicode(self):
        """Test LinkColumn for unicode values + headings"""

        class UnicodeTable(tables.Table):
            first_name = tables.LinkColumn("person", args=[A("pk")])
            last_name = tables.LinkColumn(
                "person", args=[A("pk")], verbose_name="äÚ¨´ˆÁ˜¨ˆ˜˘Ú…Ò˚ˆπ∆ˆ´"
            )

        dataset = [
            {"pk": 1, "first_name": "Brädley", "last_name": "∆yers"},
            {"pk": 2, "first_name": "Chr…s", "last_name": "DÒble"},
        ]

        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(
            Context({"request": build_request(), "table": UnicodeTable(dataset)})
        )

        self.assertIn("Brädley", html)
        self.assertIn("∆yers", html)
        self.assertIn("Chr…s", html)
        self.assertIn("DÒble", html)

    def test_link_text_custom_value(self):
        class CustomLinkTable(tables.Table):
            first_name = tables.LinkColumn("person", text="foo::bar", args=[A("pk")])
            last_name = tables.LinkColumn(
                "person",
                text=lambda row: "%s %s" % (row["last_name"], row["first_name"]),
                args=[A("pk")],
            )

        dataset = [{"pk": 1, "first_name": "John", "last_name": "Doe"}]

        html = CustomLinkTable(dataset).as_html(build_request())

        self.assertIn("foo::bar", html)
        self.assertIn("Doe John", html)

    def test_link_text_escaping(self):
        class CustomLinkTable(tables.Table):
            editlink = tables.LinkColumn("person", text=mark_safe("edit"), args=[A("pk")])

        dataset = [{"pk": 1, "first_name": "John", "last_name": "Doe"}]

        html = CustomLinkTable(dataset).as_html(build_request())

        expected = '<td ><a href="{}">edit</a></td>'.format(reverse("person", args=(1,)))
        self.assertIn(expected, html)

    def test_null_foreign_key(self):
        class PersonTable(tables.Table):
            first_name = tables.Column()
            last_name = tables.Column()
            occupation = tables.LinkColumn("occupation", args=[A("occupation__pk")])
            occupation_linkify = tables.Column(linkify=("occupation", A("occupation__pk")))

        Person.objects.create(first_name="bradley", last_name="ayers")

        table = PersonTable(Person.objects.all())
        html = table.as_html(build_request())

        self.assertIn("<td >—</td>", html)

    def test_linkcolumn_non_field_based(self):
        """Test for issue 257, non-field based columns"""

        class Table(tables.Table):
            first_name = tables.Column()
            delete_link = tables.LinkColumn(
                "person_delete", text="delete", kwargs={"pk": tables.A("id")}
            )

        willem = Person.objects.create(first_name="Willem", last_name="Wever")

        table = Table(Person.objects.all())

        expected = '<a href="{}">delete</a>'.format(
            reverse("person_delete", kwargs={"pk": willem.pk})
        )
        self.assertEqual(table.rows[0].get_cell("delete_link"), expected)

    def test_kwargs(self):
        class PersonTable(tables.Table):
            a = tables.LinkColumn("occupation", kwargs={"pk": A("a")})

        table = PersonTable([{"a": 0}, {"a": 1}])

        self.assertIn(reverse("occupation", kwargs={"pk": 0}), table.rows[0].get_cell("a"))
        self.assertIn(reverse("occupation", kwargs={"pk": 1}), table.rows[1].get_cell("a"))

    def test_html_escape_value(self):
        class PersonTable(tables.Table):
            name = tables.LinkColumn("escaping", kwargs={"pk": A("pk")})
            name_linkify = tables.Column(accessor="name", linkify=("escaping", {"pk": A("pk")}))

        table = PersonTable([{"name": "<brad>", "pk": 1}])
        # django==3.0 replaces &#39; with &#x27;, drop first option if django==2.2 support is removed
        self.assertIn(
            table.rows[0].get_cell("name"),
            (
                '<a href="/&amp;&#39;%22/1/">&lt;brad&gt;</a>'
                '<a href="/&amp;&#x27;%22/1/">&lt;brad&gt;</a>'
            ),
        )

        # the two columns should result in the same rendered cell contents
        self.assertEqual(table.rows[0].get_cell("name"), table.rows[0].get_cell("name_linkify"))

    def test_a_attrs_should_be_supported(self):
        class TestTable(tables.Table):
            attrs = {"a": {"title": "Occupation Title", "id": lambda record: str(record["id"])}}
            col = tables.LinkColumn("occupation", kwargs={"pk": A("col")}, attrs=attrs)
            col_linkify = tables.Column(
                accessor="col",
                attrs=attrs,
                linkify=("occupation", {"pk": A("col")}),
            )

        table = TestTable([{"col": 0, "id": 1}])
        self.assertEqual(
            attrs(table.rows[0].get_cell("col")),
            {
                "href": reverse("occupation", kwargs={"pk": 0}),
                "title": "Occupation Title",
                "id": "1",
            },
        )
        self.assertEqual(table.rows[0].get_cell("col"), table.rows[0].get_cell("col_linkify"))

    def test_td_attrs_should_be_supported(self):
        """LinkColumn should support both <td> and <a> attrs"""

        person = Person.objects.create(first_name="Bob", last_name="Builder")

        class Table(tables.Table):
            first_name = tables.LinkColumn(
                attrs={"a": {"style": "color: red;"}, "td": {"style": "background-color: #ddd;"}}
            )
            last_name = tables.Column()

        table = Table(Person.objects.all())

        a_tag = table.rows[0].get_cell("first_name")
        self.assertIn('href="{}"'.format(reverse("person", args=(person.pk,))), a_tag)
        self.assertIn('style="color: red;"', a_tag)
        self.assertIn(person.first_name, a_tag)

        html = table.as_html(build_request())

        self.assertIn('<td style="background-color: #ddd;">', html)

    def test_defaults(self):
        class Table(tables.Table):
            link = tables.LinkColumn("occupation", kwargs={"pk": 1}, default="xyz")

        table = Table([{}])
        self.assertEqual(table.rows[0].get_cell("link"), "xyz")

    def test_get_absolute_url(self):
        class PersonTable(tables.Table):
            first_name = tables.Column()
            last_name = tables.LinkColumn()
            other_last_name = tables.Column(accessor="last_name", linkify=True)

        person = Person.objects.create(first_name="Jan Pieter", last_name="Waagmeester")
        table = PersonTable(Person.objects.all())

        expected = '<a href="{}">{}</a>'.format(person.get_absolute_url(), person.last_name)
        self.assertEqual(table.rows[0].cells["last_name"], expected)

        # Explicit LinkColumn and regular column using linkify should have equal output
        self.assertEqual(
            table.rows[0].get_cell("other_last_name"), table.rows[0].get_cell("last_name")
        )

    def test_get_absolute_url_not_defined(self):
        """A dict doesn't have a get_absolute_url(), so creating the table should raise a TypeError."""

        class Table(tables.Table):
            first_name = tables.Column()
            last_name = tables.LinkColumn()

        table = Table([dict(first_name="Jan Pieter", last_name="Waagmeester")])

        with self.assertRaises(TypeError):
            table.as_html(build_request())

    def test_RelatedLinkColumn(self):
        carpenter = Occupation.objects.create(name="Carpenter")
        Person.objects.create(first_name="Bob", last_name="Builder", occupation=carpenter)

        class Table(tables.Table):
            occupation = tables.RelatedLinkColumn()
            occupation_linkify = tables.Column(accessor="occupation", linkify=True)

        table = Table(Person.objects.all())

        self.assertEqual(
            table.rows[0].cells["occupation"],
            '<a href="{}">Carpenter</a>'.format(reverse("occupation", args=[carpenter.pk])),
        )

    def test_RelatedLinkColumn_without_model(self):
        class Table(tables.Table):
            occupation = tables.RelatedLinkColumn()

        table = Table([{"occupation": "Fabricator"}])

        msg = "for linkify=True, 'Fabricator' must have a method get_absolute_url"
        with self.assertRaisesMessage(TypeError, msg):
            table.rows[0].cells["occupation"]

    def test_value_returns_a_raw_value_without_html(self):
        class Table(tables.Table):
            col = tables.LinkColumn("occupation", args=(A("id"),))

        table = Table([{"col": "link-text", "id": 1}])
        self.assertEqual(table.rows[0].get_cell_value("col"), "link-text")
