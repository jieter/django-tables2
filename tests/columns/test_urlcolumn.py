# coding: utf-8
from __future__ import unicode_literals

from django.db import models

import django_tables2 as tables

MEMORY_DATA = [
    {'url': 'http://example.com', 'name': 'Example'},
    {'url': 'https://example.com', 'name': 'Example (https)'},
    {'url': 'ftp://example.com', 'name': 'Example (ftp)'},
]


def test_should_turn_url_into_hyperlink():
    class TestTable(tables.Table):
        url = tables.URLColumn()

    table = TestTable(MEMORY_DATA)

    assert table.rows[0].get_cell('url') == '<a href="http://example.com">http://example.com</a>'
    assert table.rows[1].get_cell('url') == '<a href="https://example.com">https://example.com</a>'


def test_should_be_used_for_urlfields():
    class URLModel(models.Model):
        field = models.URLField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = URLModel

    assert type(Table.base_columns['field']) == tables.URLColumn


def test_text_can_be_overridden():
    class Table(tables.Table):
        url = tables.URLColumn(text='link')

    table = Table(MEMORY_DATA)

    assert table.rows[0].get_cell('url') == '<a href="http://example.com">link</a>'


def test_text_can_be_overridden_with_callable():
    class Table(tables.Table):
        url = tables.URLColumn(text=lambda record: record['name'])

    table = Table(MEMORY_DATA)

    assert table.rows[0].get_cell('url') == '<a href="http://example.com">Example</a>'
    assert table.rows[1].get_cell('url') == '<a href="https://example.com">Example (https)</a>'
