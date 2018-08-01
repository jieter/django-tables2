# coding: utf-8
from __future__ import unicode_literals

from django.template import Context, Template
from django.test import SimpleTestCase

import django_tables2 as tables

from ..utils import build_request


class TemplateColumnTest(SimpleTestCase):
    def test_should_render_in_pinned_row(self):
        class TestOnlyPinnedTable(tables.Table):
            foo = tables.TemplateColumn("value={{ value }}")

            def __init__(self, data):
                self.pinned = data
                revised_data = []

                super(TestOnlyPinnedTable, self).__init__(revised_data)

            def get_top_pinned_data(self):
                return self.pinned

        table = TestOnlyPinnedTable([{"foo": "bar"}])
        for row in table.rows:
            self.assertEqual(row.get_cell("foo"), "value=bar")

        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(Context({"request": build_request(), "table": table}))

        self.assertIn("<td >value=bar</td>", html)

    def test_should_handle_context_on_table(self):
        class TestTable(tables.Table):
            col_code = tables.TemplateColumn(template_code="code:{{ record.col }}-{{ foo }}")
            col_name = tables.TemplateColumn(template_name="test_template_column.html")
            col_context = tables.TemplateColumn(
                template_code="{{ label }}:{{ record.col }}-{{ foo }}",
                extra_context={"label": "label"},
            )

        table = TestTable([{"col": "brad"}])
        self.assertEqual(table.rows[0].get_cell("col_code"), "code:brad-")
        self.assertEqual(table.rows[0].get_cell("col_name"), "name:brad-empty\n")
        self.assertEqual(table.rows[0].get_cell("col_context"), "label:brad-")

        table.context = Context({"foo": "author"})
        self.assertEqual(table.rows[0].get_cell("col_code"), "code:brad-author")
        self.assertEqual(table.rows[0].get_cell("col_name"), "name:brad-author\n")
        self.assertEqual(table.rows[0].get_cell("col_context"), "label:brad-author")

        # new table and render using the 'render_table' template tag.
        table = TestTable([{"col": "brad"}])
        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(
            Context({"request": build_request(), "table": table, "foo": "author"})
        )

        self.assertIn("<td >name:brad-author\n</td>", html)

    def test_should_support_default(self):
        class Table(tables.Table):
            foo = tables.TemplateColumn("default={{ default }}", default="bar")

        table = Table([{}])
        self.assertEqual(table.rows[0].get_cell("foo"), "default=bar")

    def test_should_support_value(self):
        class Table(tables.Table):
            foo = tables.TemplateColumn("value={{ value }}")

        table = Table([{"foo": "bar"}])
        self.assertEqual(table.rows[0].get_cell("foo"), "value=bar")

        template = Template("{% load django_tables2 %}{% render_table table %}")
        html = template.render(Context({"request": build_request(), "table": table}))

        self.assertIn("<td >value=bar</td>", html)

    def test_should_support_column(self):
        class Table(tables.Table):
            tcol = tables.TemplateColumn("column={{ column.name }}")

        table = Table([{"foo": "bar"}])
        self.assertEqual(table.rows[0].get_cell("tcol"), "column=tcol")

    def test_should_raise_when_called_without_template(self):
        with self.assertRaises(ValueError):

            class Table(tables.Table):
                col = tables.TemplateColumn()

    def test_should_support_value_with_curly_braces(self):
        """
        https://github.com/bradleyayers/django-tables2/issues/441
        """

        class Table(tables.Table):
            track = tables.TemplateColumn("track: {{ value }}")

        table = Table([{"track": "Beat it {Freestyle}"}])
        self.assertEqual(table.rows[0].get_cell("track"), "track: Beat it {Freestyle}")

    def test_should_strip_tags_for_value(self):
        class Table(tables.Table):
            track = tables.TemplateColumn("<span>{{ value }}</span>")

        table = Table([{"track": "Space Oddity"}])

        self.assertEqual(list(table.as_values()), [["Track"], ["Space Oddity"]])
