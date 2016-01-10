# coding: utf-8
# pylint: disable=R0912,E0102
from __future__ import unicode_literals

from django.db import models

import django_tables2 as tables


def test_should_turn_url_into_hyperlink():
    class TestTable(tables.Table):
        url = tables.URLColumn()

    table = TestTable([{"url": "http://example.com"}])
    assert table.rows[0]["url"] == '<a href="http://example.com">http://example.com</a>'


def test_should_be_used_for_urlfields():
    class URLModel(models.Model):
        field = models.URLField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = URLModel

    assert type(Table.base_columns["field"]) == tables.URLColumn
