# coding: utf-8
from __future__ import unicode_literals

import os

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.fields.files import FieldFile
from django.test import SimpleTestCase

import django_tables2 as tables

from ..utils import parse


def storage():
    """Provide a storage that exposes the test templates"""
    root = os.path.join(os.path.dirname(__file__), "..", "app", "templates")
    return FileSystemStorage(location=root, base_url="/baseurl/")


def column():
    return tables.FileColumn(attrs={"span": {"class": "span"}, "a": {"class": "a"}})


class FileColumnTest(SimpleTestCase):
    def test_should_be_used_for_filefields(self):
        class FileModel(models.Model):
            field = models.FileField()

            class Meta:
                app_label = "django_tables2_test"

        class Table(tables.Table):
            class Meta:
                model = FileModel

        self.assertEqual(type(Table.base_columns["field"]), tables.FileColumn)

    def test_filecolumn_supports_storage_file(self):
        file_ = storage().open("child/foo.html")
        try:
            root = parse(column().render(value=file_, record=None))
        finally:
            file_.close()

        self.assertEqual(root.tag, "span")
        self.assertEqual(root.attrib, {"class": "span exists", "title": file_.name})
        self.assertEqual(root.text, "foo.html")

    def test_filecolumn_supports_contentfile(self):
        name = "foobar.html"
        file_ = ContentFile("")
        file_.name = name

        root = parse(column().render(value=file_, record=None))
        self.assertEqual(root.tag, "span")
        self.assertEqual(root.attrib, {"title": name, "class": "span"})
        self.assertEqual(root.text, "foobar.html")

    def test_filecolumn_supports_fieldfile(self):
        field = models.FileField(storage=storage())
        name = "child/foo.html"

        class Table(tables.Table):
            filecolumn = column()

        table = Table([{"filecolumn": FieldFile(instance=None, field=field, name=name)}])
        html = table.rows[0].get_cell("filecolumn")
        root = parse(html)

        self.assertEqual(root.tag, "a")
        self.assertEqual(root.attrib, {"class": "a", "href": "/baseurl/child/foo.html"})
        span = root.find("span")
        self.assertEqual(span.tag, "span")
        self.assertEqual(span.text, "foo.html")

        # Now try a file that doesn't exist
        name = "child/does_not_exist.html"
        fieldfile = FieldFile(instance=None, field=field, name=name)
        root = parse(column().render(value=fieldfile, record=None))

        self.assertEqual(root.tag, "span")
        self.assertEqual(root.attrib, {"class": "span missing", "title": name})
        self.assertEqual(root.text, "does_not_exist.html")

    def test_filecolumn_text_custom_value(self):
        file_ = ContentFile("")
        file_.name = "foobar.html"

        root = parse(tables.FileColumn(text="Download").render(value=file_, record=None))
        self.assertEqual(root.tag, "span")
        self.assertEqual(root.attrib, {"title": file_.name, "class": ""})
        self.assertEqual(root.text, "Download")
