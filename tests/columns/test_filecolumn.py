# coding: utf-8
from __future__ import unicode_literals

from os.path import dirname, join

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.fields.files import FieldFile
from django.test import SimpleTestCase

import django_tables2 as tables

from ..utils import parse


def storage():
    '''Provide a storage that exposes the test templates'''
    root = join(dirname(__file__), '..', 'app', 'templates')
    return FileSystemStorage(location=root, base_url='/baseurl/')


def column():
    return tables.FileColumn(attrs={
        'span': {'class': 'span'},
        'a': {'class': 'a'}
    })


class FileColumnTest(SimpleTestCase):
    def test_should_be_used_for_filefields(self):
        class FileModel(models.Model):
            field = models.FileField()

            class Meta:
                app_label = 'django_tables2_test'

        class Table(tables.Table):
            class Meta:
                model = FileModel

        assert type(Table.base_columns['field']) == tables.FileColumn

    def test_filecolumn_supports_storage_file(self):
        file_ = storage().open('child/foo.html')
        try:
            root = parse(column().render(value=file_, record=None))
        finally:
            file_.close()
        path = file_.name
        assert root.tag == 'span'
        assert root.attrib == {'class': 'span exists', 'title': path}
        assert root.text == 'foo.html'

    def test_filecolumn_supports_contentfile(self):
        name = 'foobar.html'
        file_ = ContentFile('')
        file_.name = name
        root = parse(column().render(value=file_, record=None))
        assert root.tag == 'span'
        assert root.attrib == {'title': name, 'class': 'span'}
        assert root.text == 'foobar.html'

    def test_filecolumn_supports_fieldfile(self):
        field = models.FileField(storage=storage())
        name = 'child/foo.html'
        fieldfile = FieldFile(instance=None, field=field, name=name)
        root = parse(column().render(value=fieldfile, record=None))
        assert root.tag == 'a'
        assert root.attrib == {
            'class': 'a exists',
            'title': name,
            'href': '/baseurl/child/foo.html'
        }
        assert root.text == 'foo.html'

        # Now try a file that doesn't exist
        name = 'child/does_not_exist.html'
        fieldfile = FieldFile(instance=None, field=field, name=name)
        html = column().render(value=fieldfile, record=None)
        root = parse(html)
        assert root.tag == 'a'
        assert root.attrib == {
            'class': 'a missing',
            'title': name,
            'href': '/baseurl/child/does_not_exist.html'
        }
        assert root.text == 'does_not_exist.html'

    def test_filecolumn_text_custom_value(self):
        name = 'foobar.html'
        file_ = ContentFile('')
        file_.name = name
        root = parse(tables.FileColumn(text='Download').render(value=file_, record=None))
        assert root.tag == 'span'
        assert root.attrib == {'title': name, 'class': ''}
        assert root.text == 'Download'
