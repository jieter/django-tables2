# coding: utf-8
# pylint: disable=R0912,E0102
from __future__ import unicode_literals

from os.path import dirname, join

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models.fields.files import FieldFile

import django_tables2 as tables
import pytest

from ..utils import parse


@pytest.yield_fixture
def storage():
    """Provide a storage that exposes the test templates"""
    root = join(dirname(__file__), '..', 'app', 'templates')
    yield FileSystemStorage(location=root, base_url='/baseurl/')


@pytest.yield_fixture
def column():
    yield tables.FileColumn(attrs={
        'span': {'class': 'span'},
        'a': {'class': 'a'}
    })


def test_should_be_used_for_filefields():
    class FileModel(models.Model):
        field = models.FileField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = FileModel

    assert type(Table.base_columns['field']) == tables.FileColumn


def test_filecolumn_supports_storage_file(column, storage):
    file_ = storage.open('child/foo.html')
    try:
        root = parse(column.render(value=file_))
    finally:
        file_.close()
    path = file_.name
    assert root.tag == 'span'
    assert root.attrib == {'class': 'span exists', 'title': path}
    assert root.text == 'foo.html'


def test_filecolumn_supports_contentfile(column):
    name = "foobar.html"
    file_ = ContentFile('')
    file_.name = name
    root = parse(column.render(value=file_))
    assert root.tag == 'span'
    assert root.attrib == {'title': name, 'class': 'span'}
    assert root.text == 'foobar.html'


def test_filecolumn_supports_fieldfile(column, storage):
    field = models.FileField(storage=storage)
    name = "child/foo.html"
    fieldfile = FieldFile(instance=None, field=field, name=name)
    root = parse(column.render(value=fieldfile))
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
    html = column.render(value=fieldfile)
    root = parse(html)
    assert root.tag == 'a'
    assert root.attrib == {
        'class': 'a missing',
        'title': name,
        'href': '/baseurl/child/does_not_exist.html'
    }
    assert root.text == 'does_not_exist.html'
