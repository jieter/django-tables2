# coding: utf-8
from __future__ import unicode_literals

from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import Paginator
from django.template import Context, RequestContext, Template, TemplateSyntaxError
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import six
from django.utils.six.moves.urllib.parse import parse_qs

from django_tables2 import LazyPaginator, RequestConfig, Table, TemplateColumn
from django_tables2.export import ExportMixin
from django_tables2.templatetags.django_tables2 import table_page_range
from django_tables2.utils import AttributeDict

from .app.models import Region
from .test_templates import MEMORY_DATA, CountryTable
from .utils import build_request, parse


class RenderTableTagTest(TestCase):
    def test_invalid_type(self):
        template = Template("{% load django_tables2 %}{% render_table table %}")

        with self.assertRaises(ValueError):
            template.render(Context({"request": build_request(), "table": dict()}))

    def test_basic(self):
        request = build_request("/")
        # ensure it works with a multi-order-by
        table = CountryTable(MEMORY_DATA, order_by=("name", "population"))
        RequestConfig(request).configure(table)
        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(Context({"request": request, "table": table}))

        root = parse(html)
        self.assertEqual(len(root.findall(".//thead/tr")), 1)
        self.assertEqual(len(root.findall(".//thead/tr/th")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 16)

    def test_does_not_mutate_context(self):
        """
        Make sure the tag does not change the context of the template the tag is called from
        https://github.com/jieter/django-tables2/issues/547
        """

        class MyTable(Table):
            col = TemplateColumn(template_code="{{ value }}")

        table = MyTable([{"col": "foo"}, {"col": "bar"}], template_name="minimal.html")
        template = Template(
            "{% load django_tables2 %}"
            '{% with "foo" as table %}{{ table }}{% render_table mytable %}\n{{ table }}{% endwith %}'
        )

        html = template.render(Context({"request": build_request(), "mytable": table}))
        lines = html.splitlines()
        self.assertEqual(lines[0], "foo")
        self.assertEqual(lines[-1], "foo")

    def test_table_context_is_RequestContext(self):
        class MyTable(Table):
            col = TemplateColumn(template_code="{{ value }}")

        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(
            Context({"request": build_request(), "table": MyTable([], template_name="csrf.html")})
        )
        input_tag = parse(html)
        self.assertEqual(input_tag.get("type"), "hidden")
        self.assertEqual(input_tag.get("name"), "csrfmiddlewaretoken")
        self.assertEqual(len(input_tag.get("value")), 64)

    def test_no_data_without_empty_text(self):
        table = CountryTable([])
        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(Context({"request": build_request("/"), "table": table}))
        root = parse(html)
        self.assertEqual(len(root.findall(".//thead/tr")), 1)
        self.assertEqual(len(root.findall(".//thead/tr/th")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr")), 0)

    def test_no_data_with_empty_text(self):
        # no data WITH empty_text
        request = build_request("/")
        table = CountryTable([], empty_text="this table is empty")
        RequestConfig(request).configure(table)
        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(Context({"request": request, "table": table}))

        root = parse(html)
        self.assertEqual(len(root.findall(".//thead/tr")), 1)
        self.assertEqual(len(root.findall(".//thead/tr/th")), 4)
        self.assertEqual(len(root.findall(".//tbody/tr")), 1)
        self.assertEqual(len(root.findall(".//tbody/tr/td")), 1)
        self.assertEqual(
            int(root.find(".//tbody/tr/td").get("colspan")), len(root.findall(".//thead/tr/th"))
        )
        self.assertEqual(root.find(".//tbody/tr/td").text, "this table is empty")

    @override_settings(DEBUG=True)
    def test_missing_variable(self):
        # variable that doesn't exist (issue #8)
        template = Template("{% load django_tables2 %}{% render_table this_doesnt_exist %}")
        with self.assertRaises(ValueError):
            template.render(Context())

    @override_settings(DEBUG=False)
    def test_missing_variable_debug_False(self):
        template = Template("{% load django_tables2 %}{% render_table this_doesnt_exist %}")
        # Should still be noisy with debug off
        with self.assertRaises(ValueError):
            template.render(Context())

    def test_should_support_template_argument(self):
        table = CountryTable(MEMORY_DATA, order_by=("name", "population"))
        template = Template("{% load django_tables2 %}" '{% render_table table "dummy.html" %}')

        context = RequestContext(build_request(), {"table": table})
        self.assertEqual(template.render(context), "dummy template contents\n")

    def test_template_argument_list(self):
        template = Template("{% load django_tables2 %}" "{% render_table table template_list %}")

        context = RequestContext(
            build_request(),
            {
                "table": CountryTable(MEMORY_DATA, order_by=("name", "population")),
                "template_list": ("dummy.html", "child/foo.html"),
            },
        )
        self.assertEqual(template.render(context), "dummy template contents\n")

    def test_render_table_supports_queryset(self):
        for name in ("Mackay", "Brisbane", "Maryborough"):
            Region.objects.create(name=name)
        template = Template("{% load django_tables2 %}{% render_table qs %}")
        html = template.render(Context({"qs": Region.objects.all(), "request": build_request("/")}))

        root = parse(html)
        self.assertEqual(
            [e.text for e in root.findall(".//thead/tr/th/a")], ["ID", "Name", "Mayor"]
        )
        td = [[td.text for td in tr.findall("td")] for tr in root.findall(".//tbody/tr")]
        db = []
        for region in Region.objects.all():
            db.append([six.text_type(region.id), region.name, "—"])
        self.assertEqual(td, db)


class QuerystringTagTest(SimpleTestCase):
    def test_basic(self):
        template = Template(
            "{% load django_tables2 %}" '<b>{% querystring "name"="Brad" foo.bar=value %}</b>'
        )

        # Should be something like: <root>?name=Brad&amp;a=b&amp;c=5&amp;age=21</root>
        xml = template.render(
            Context(
                {"request": build_request("/?a=b&name=dog&c=5"), "foo": {"bar": "age"}, "value": 21}
            )
        )

        # Ensure it's valid XML, retrieve the URL
        url = parse(xml).text

        qs = parse_qs(url[1:])  # everything after the ?
        self.assertEqual(qs["name"], ["Brad"])
        self.assertEqual(qs["age"], ["21"])
        self.assertEqual(qs["a"], ["b"])
        self.assertEqual(qs["c"], ["5"])

    def test_requires_request(self):
        template = Template('{% load django_tables2 %}{% querystring "name"="Brad" %}')
        with self.assertRaises(ImproperlyConfigured):
            template.render(Context())

    def test_supports_without(self):
        context = Context({"request": build_request("/?a=b&name=dog&c=5"), "a_var": "a"})

        template = Template(
            "{% load django_tables2 %}" '<b>{% querystring "name"="Brad" without a_var %}</b>'
        )
        url = parse(template.render(context)).text
        qs = parse_qs(url[1:])  # trim the ?
        self.assertEqual(set(qs.keys()), set(["name", "c"]))

    def test_only_without(self):
        context = Context({"request": build_request("/?a=b&name=dog&c=5"), "a_var": "a"})
        template = Template(
            "{% load django_tables2 %}" '<b>{% querystring without "a" "name" %}</b>'
        )
        url = parse(template.render(context)).text
        qs = parse_qs(url[1:])  # trim the ?
        self.assertEqual(set(qs.keys()), set(["c"]))

    def test_querystring_syntax_error(self):
        with self.assertRaises(TemplateSyntaxError):
            Template("{% load django_tables2 %}{% querystring foo= %}")

    def test_querystring_as_var(self):
        def assert_querystring_asvar(template_code, expected):
            template = Template(
                "{% load django_tables2 %}"
                + "<b>{% querystring "
                + template_code
                + " %}</b>"
                + "<strong>{{ varname }}</strong>"
            )

            # Should be something like: <root>?name=Brad&amp;a=b&amp;c=5&amp;age=21</root>
            xml = template.render(
                Context({"request": build_request("/?a=b"), "foo": {"bar": "age"}, "value": 21})
            )
            self.assertIn("<b></b>", xml)
            qs = parse(xml).xpath(".//strong")[0].text[1:]
            self.assertEqual(parse_qs(qs), expected)

        tests = (
            ('"name"="Brad" as=varname', dict(name=["Brad"], a=["b"])),
            ('as=varname "name"="Brad"', dict(name=["Brad"], a=["b"])),
            ('"name"="Brad" as=varname without "a" ', dict(name=["Brad"])),
        )

        for argstr, expected in tests:
            assert_querystring_asvar(argstr, expected)

    def test_export_url_tag(self):
        class View(ExportMixin):
            export_trigger_param = "_do_export"

        template = Template('{% load django_tables2 %}{% export_url "csv" %}')
        html = template.render(Context({"request": build_request("?q=foo"), "view": View()}))
        self.assertEqual(dict(parse_qs(html[1:])), dict(parse_qs("q=foo&amp;_do_export=csv")))

        # using a template context variable and a view
        template = Template("{% load django_tables2 %}{% export_url format %}")
        html = template.render(
            Context({"request": build_request("?q=foo"), "format": "xls", "view": View()})
        )
        self.assertEqual(dict(parse_qs(html[1:])), dict(parse_qs("q=foo&amp;_do_export=xls")))

        # using a template context variable
        template = Template("{% load django_tables2 %}{% export_url format %}")
        html = template.render(Context({"request": build_request("?q=foo"), "format": "xls"}))
        self.assertEqual(dict(parse_qs(html[1:])), dict(parse_qs("q=foo&amp;_export=xls")))

        # using a template context and change export parameter
        template = Template('{% load django_tables2 %}{% export_url "xls" "_other_export_param" %}')
        html = template.render(Context({"request": build_request("?q=foo"), "format": "xls"}))
        self.assertEqual(
            dict(parse_qs(html[1:])), dict(parse_qs("q=foo&amp;_other_export_param=xls"))
        )

    def test_render_attributes_test(self):
        template = Template('{% load django_tables2 %}{% render_attrs attrs class="table" %}')
        html = template.render(Context({}))
        self.assertEqual(html, 'class="table"')

        html = template.render(Context({"attrs": AttributeDict({"class": "table table-striped"})}))
        self.assertEqual(html, 'class="table table-striped"')


class TablePageRangeTest(SimpleTestCase):
    def test_table_page_range(self):
        paginator = Paginator(range(1, 1000), 10)
        self.assertEqual(
            table_page_range(paginator.page(1), paginator), [1, 2, 3, 4, 5, 6, 7, 8, "...", 100]
        )
        self.assertEqual(
            table_page_range(paginator.page(10), paginator),
            [1, "...", 7, 8, 9, 10, 11, 12, "...", 100],
        )
        self.assertEqual(
            table_page_range(paginator.page(100), paginator),
            [1, "...", 93, 94, 95, 96, 97, 98, 99, 100],
        )

    def test_table_page_range_num_pages_equals_page_range_plus_one(self):
        paginator = Paginator(range(1, 11*10), 10)
        self.assertEqual(
            table_page_range(paginator.page(1), paginator), [1, 2, 3, 4, 5, 6, 7, 8, "...", 11]
        )
        self.assertEqual(
            table_page_range(paginator.page(6), paginator),
            [1, 2, 3, 4, 5, 6, 7, 8, "...", 11],
        )
        self.assertEqual(
            table_page_range(paginator.page(7), paginator),
            [1, "...", 4, 5, 6, 7, 8, 9, 10, 11],
        )

    def test_table_page_range_lazy(self):
        paginator = LazyPaginator(range(1, 1000), 10)

        self.assertEqual(table_page_range(paginator.page(1), paginator), range(1, 3))
        self.assertEqual(
            table_page_range(paginator.page(10), paginator), [1, "...", 4, 5, 6, 7, 8, 9, 10, 11]
        )
