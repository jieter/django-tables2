from django.contrib.postgres.fields import HStoreField
from django.db import models
from django.test import SimpleTestCase

import django_tables2 as tables

try:
    from django.db.models import JSONField  # django==3.1 moved json field
except ImportError:
    from django.contrib.postgres.fields import JSONField


class JsonColumnTestCase(SimpleTestCase):
    def test_should_be_used_for_json_and_hstore_fields(self):
        class Model(models.Model):
            json = JSONField()
            hstore = HStoreField()

            class Meta:
                app_label = "django_tables2_test"

        class Table(tables.Table):
            class Meta:
                model = Model

        self.assertIsInstance(Table.base_columns["json"], tables.JSONColumn)
        self.assertIsInstance(Table.base_columns["hstore"], tables.JSONColumn)

    def test_jsoncolumn_attrs(self):
        column = tables.JSONColumn(attrs={"pre": {"class": "json"}})

        record = {"json": "foo"}
        html = column.render(value=record["json"], record=record)
        self.assertEqual(html, '<pre class="json">&quot;foo&quot;</pre>')

    def test_jsoncolumn_dict(self):
        column = tables.JSONColumn()

        record = {"json": {"species": "Falcon"}}
        html = column.render(value=record["json"], record=record)
        self.assertEqual(html, "<pre >{\n  &quot;species&quot;: &quot;Falcon&quot;\n}</pre>")

    def test_jsoncolumn_string(self):
        column = tables.JSONColumn()

        record = {"json": "really?"}
        html = column.render(value=record["json"], record=record)
        self.assertEqual(html, "<pre >&quot;really?&quot;</pre>")

    def test_jsoncolumn_number(self):
        column = tables.JSONColumn()

        record = {"json": 3.14}
        html = column.render(value=record["json"], record=record)
        self.assertEqual(html, "<pre >3.14</pre>")
