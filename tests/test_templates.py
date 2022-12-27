from django.template import Context, Template
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils.translation import gettext_lazy, override as translation_override
from lxml import etree

import django_tables2 as tables
from django_tables2.config import RequestConfig

from .app.models import Person
from .utils import build_request, parse


class CountryTable(tables.Table):
    name = tables.Column()
    capital = tables.Column(orderable=False, verbose_name=gettext_lazy("Capital"))
    population = tables.Column(verbose_name="Population Size")
    currency = tables.Column(visible=False)
    tld = tables.Column(visible=False, verbose_name="Domain")
    calling_code = tables.Column(accessor="cc", verbose_name="Phone Ext.")


MEMORY_DATA = [
    {
        "name": "Germany",
        "capital": "Berlin",
        "population": 83,
        "currency": "Euro (€)",
        "tld": "de",
        "cc": 49,
    },
    {"name": "France", "population": 64, "currency": "Euro (€)", "tld": "fr", "cc": 33},
    {"name": "Netherlands", "capital": "Amsterdam", "cc": "31"},
    {"name": "Austria", "cc": 43, "currency": "Euro (€)", "population": 8},
]


class TemplateTest(TestCase):
    @override_settings(DJANGO_TABLES2_TEMPLATE="foo/bar.html")
    def test_template_override_in_settings(self):
        class Table(tables.Table):
            column = tables.Column()

        table = Table({})
        self.assertEqual(table.template_name, "foo/bar.html")

    def test_as_html(self):
        request = build_request("/")
        table = CountryTable(MEMORY_DATA)
        root = parse(table.as_html(request))
        self.assertEqual(len(root.findall(".//thead/tr")), 1)
        self.assertEqual(len(root.findall(".//thead/tr/th")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 16)

        # no data with no empty_text
        table = CountryTable([])
        root = parse(table.as_html(request))
        self.assertEqual(1, len(root.findall(".//thead/tr")))
        self.assertEqual(4, len(root.findall(".//thead/tr/th")))
        self.assertEqual(0, len(root.findall(".//tbody/tr")))

        # no data WITH empty_text
        table = CountryTable([], empty_text="this table is empty")
        root = parse(table.as_html(request))
        self.assertEqual(1, len(root.findall(".//thead/tr")))
        self.assertEqual(4, len(root.findall(".//thead/tr/th")))
        self.assertEqual(1, len(root.findall(".//tbody/tr")))
        self.assertEqual(1, len(root.findall(".//tbody/tr/td")))
        self.assertEqual(
            int(root.find(".//tbody/tr/td").get("colspan")), len(root.findall(".//thead/tr/th"))
        )
        self.assertEqual(root.find(".//tbody/tr/td").text, "this table is empty")

        # data without header
        table = CountryTable(MEMORY_DATA, show_header=False)
        root = parse(table.as_html(request))
        self.assertEqual(len(root.findall(".//thead")), 0)
        self.assertEqual(len(root.findall(".//tbody/tr")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 16)

        # with custom template
        table = CountryTable([], template_name="django_tables2/table.html")
        table.as_html(request)

    def test_custom_rendering(self):
        """For good measure, render some actual templates."""
        countries = CountryTable(MEMORY_DATA)
        context = Context({"countries": countries})

        # automatic and manual column verbose names
        template = Template(
            "{% for column in countries.columns %}{{ column }}/" "{{ column.name }} {% endfor %}"
        )
        result = "Name/name Capital/capital Population Size/population " "Phone Ext./calling_code "
        assert result == template.render(context)

        # row values
        template = Template(
            "{% for row in countries.rows %}{% for value in row %}"
            "{{ value }} {% endfor %}{% endfor %}"
        )
        result = "Germany Berlin 83 49 France — 64 33 Netherlands Amsterdam " "— 31 Austria — 8 43 "
        assert result == template.render(context)


class TestQueries(TestCase):
    def test_as_html_db_queries(self):
        class PersonTable(tables.Table):
            class Meta:
                model = Person

        request = build_request("/")

        with self.assertNumQueries(1):
            PersonTable(Person.objects.all()).as_html(request)

    def test_render_table_db_queries(self):
        """
        Paginated tables should result in two queries:
         - one query for pagination: .count()
         - one query for records on the current page: .all()[start:end]
        """
        Person.objects.create(first_name="brad", last_name="ayers")
        Person.objects.create(first_name="davina", last_name="adisusila")

        class PersonTable(tables.Table):
            class Meta:
                model = Person
                per_page = 1

        request = build_request("/")

        with self.assertNumQueries(2):
            request = build_request("/")
            table = PersonTable(Person.objects.all())
            RequestConfig(request).configure(table)
            html = Template("{% load django_tables2 %}{% render_table table %}").render(
                Context({"table": table, "request": request})
            )

            self.assertIn("brad", html)
            self.assertIn("ayers", html)


class TemplateLocalizeTest(TestCase):
    simple_test_data = [{"name": 1234.5}]
    expected_results = {None: "1234.5", False: "1234.5", True: "1 234,5"}  # non-breaking space

    def assert_cond_localized_table(self, localizeit=None, expected=None):
        """
        helper function for defining Table class conditionally
        """

        class TestTable(tables.Table):
            name = tables.Column(verbose_name="my column", localize=localizeit)

        self.assert_table_localization(TestTable, expected)

    def assert_table_localization(self, TestTable, expected):
        html = TestTable(self.simple_test_data).as_html(build_request())
        self.assertIn(f"<td >{self.expected_results[expected]}</td>", html)

    def test_localization_check(self):
        self.assert_cond_localized_table(None, None)
        # unlocalize
        self.assert_cond_localized_table(False, False)

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_localization_different_locale(self):
        with translation_override("pl"):
            # with default polish locales and enabled thousand separator
            # 1234.5 is formatted as "1 234,5" with nbsp
            self.assert_cond_localized_table(True, True)

            # with localize = False there should be no formatting
            self.assert_cond_localized_table(False, False)

            # with localize = None and USE_L10N = True
            # there should be the same formatting as with localize = True
            self.assert_cond_localized_table(None, True)

    def test_localization_check_in_meta(self):
        class TableNoLocalize(tables.Table):
            name = tables.Column(verbose_name="my column")

            class Meta:
                default = "---"

        self.assert_table_localization(TableNoLocalize, None)

    @override_settings(USE_L10N=True, USE_THOUSAND_SEPARATOR=True)
    def test_localization_check_in_meta_different_locale(self):
        class TableNoLocalize(tables.Table):
            name = tables.Column(verbose_name="my column")

            class Meta:
                default = "---"

        class TableLocalize(tables.Table):
            name = tables.Column(verbose_name="my column")

            class Meta:
                default = "---"
                localize = ("name",)

        class TableUnlocalize(tables.Table):
            name = tables.Column(verbose_name="my column")

            class Meta:
                default = "---"
                unlocalize = ("name",)

        class TableLocalizePrecedence(tables.Table):
            name = tables.Column(verbose_name="my column")

            class Meta:
                default = "---"
                unlocalize = ("name",)
                localize = ("name",)

        with translation_override("pl"):
            # the same as in localization_check.
            # with localization and polish locale we get formatted output
            self.assert_table_localization(TableNoLocalize, True)

            # localize
            self.assert_table_localization(TableLocalize, True)

            # unlocalize
            self.assert_table_localization(TableUnlocalize, False)

            # test unlocalize has higher precedence
            self.assert_table_localization(TableLocalizePrecedence, False)

    def test_localization_of_pagination_strings(self):
        class Table(tables.Table):
            foo = tables.Column(verbose_name="my column")
            bar = tables.Column()

            class Meta:
                default = "---"

        table = Table(map(lambda x: [x, x + 100], range(40)))
        request = build_request("/?page=2")
        RequestConfig(request, paginate={"per_page": 10}).configure(table)

        with translation_override("en"):
            html = table.as_html(request)
            self.assertIn("previous", html)
            self.assertIn("next", html)

        with translation_override("nl"):
            html = table.as_html(request)
            self.assertIn("vorige", html)
            self.assertIn("volgende", html)

        with translation_override("fr"):
            html = table.as_html(request)
            self.assertIn("précédent", html)
            self.assertIn("suivant", html)


class BootstrapTable(CountryTable):
    class Meta:
        template_name = "django_tables2/bootstrap.html"
        prefix = "bootstrap-"
        per_page = 2


class BootstrapTemplateTest(SimpleTestCase):
    def test_bootstrap_template(self):
        table = BootstrapTable(MEMORY_DATA)
        request = build_request("/")
        RequestConfig(request).configure(table)

        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(Context({"request": request, "table": table}))

        root = parse(html)
        self.assertEqual(root.find(".//table").attrib, {"class": "table"})

        self.assertEqual(len(root.findall(".//thead/tr")), 1)
        self.assertEqual(len(root.findall(".//thead/tr/th")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr")), 2)
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 8)

        self.assertEqual(root.find('.//ul[@class="pagination"]/li[2]/a').text.strip(), "2")
        # make sure the link is prefixed
        self.assertEqual(
            root.find('.//ul[@class="pagination"]/li[@class="next"]/a').get("href"),
            "?bootstrap-page=2",
        )

    def test_bootstrap_responsive_template(self):
        class BootstrapResponsiveTable(BootstrapTable):
            class Meta(BootstrapTable.Meta):
                template_name = "django_tables2/bootstrap-responsive.html"

        table = BootstrapResponsiveTable(MEMORY_DATA)
        request = build_request("/")
        RequestConfig(request).configure(table)

        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(Context({"request": request, "table": table}))
        root = parse(html)
        self.assertEqual(len(root.findall(".//thead/tr")), 1)
        self.assertEqual(len(root.findall(".//thead/tr/th")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr")), 2)
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 8)

        self.assertEqual(root.find('.//ul[@class="pagination"]/li[2]/a').text.strip(), "2")


class SemanticTemplateTest(SimpleTestCase):
    def test_semantic_template(self):
        class SemanticTable(CountryTable):
            class Meta:
                template_name = "django_tables2/semantic.html"
                prefix = "semantic-"
                per_page = 2

        table = SemanticTable(MEMORY_DATA)
        request = build_request("/")
        RequestConfig(request).configure(table)

        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(Context({"request": request, "table": table}))
        root = parse(html)
        self.assertEqual(len(root.findall(".//thead/tr")), 1)
        self.assertEqual(len(root.findall(".//thead/tr/th")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr")), 2)
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 8)

        # make sure the link is prefixed
        next_page = './/tfoot/tr/th/div[@class="ui right floated pagination menu"]/a[1]'
        self.assertEqual(root.find(next_page).get("href"), "?semantic-page=1")


class ValidHTMLTest(SimpleTestCase):
    template = """<!doctype html>
<html>
<head>
    <title>Basic html template to render a table</title>
</head>
<body>
    {% load django_tables2 %}{% render_table table %}
</body>
</html>
"""
    allowed_errors = {etree.ErrorTypes.HTML_UNKNOWN_TAG: ["Tag nav invalid"]}
    context_lines = 4

    def test_templates(self):
        parser = etree.HTMLParser()

        for name in ("table", "semantic", "bootstrap", "bootstrap4", "bootstrap5"):
            table = CountryTable(
                list([MEMORY_DATA] * 10), template_name=f"django_tables2/{name}.html"
            ).paginate(per_page=5)

            html = Template(self.template).render(
                Context({"request": build_request(), "table": table})
            )

            # will raise lxml.etree.XMLSyntaxError if markup is incorrect
            etree.fromstring(html, parser)

            for error in parser.error_log:
                if (
                    error.type in self.allowed_errors
                    and error.message in self.allowed_errors[error.type]
                ):
                    continue

                lines = html.splitlines()
                start, end = (
                    max(0, error.line - self.context_lines),
                    min(error.line + self.context_lines, len(lines)),
                )
                context = "\n".join(
                    [f"{i}: {line}" for i, line in zip(range(start + 1, end + 1), lines[start:end])]
                )
                raise AssertionError(f"template: {table.template_name}; {error} \n {context}")
