# coding: utf-8
from __future__ import unicode_literals

from django.db import models

import django_tables2 as tables


def test_should_turn_email_address_into_hyperlink():
    class Table(tables.Table):
        email = tables.EmailColumn()

    table = Table([{'email': 'test@example.com'}])
    assert table.rows[0].get_cell('email') == '<a href="mailto:test@example.com">test@example.com</a>'


def test_should_render_default_for_blank():
    class Table(tables.Table):
        email = tables.EmailColumn(default='---')

    table = Table([{'email': ''}])
    assert table.rows[0].get_cell('email') == '---'


def test_should_be_used_for_emailfields():
    class EmailModel(models.Model):
        field = models.EmailField()

        class Meta:
            app_label = 'django_tables2_test'

    class Table(tables.Table):
        class Meta:
            model = EmailModel

    assert type(Table.base_columns['field']) == tables.EmailColumn


def test_text_should_be_overridable():
    class Table(tables.Table):
        email = tables.EmailColumn(text='@')

    table = Table([{'email': 'test@example.com'}])
    assert table.rows[0].get_cell('email') == '<a href="mailto:test@example.com">@</a>'


def test_value_returns_a_raw_value_without_html():
    class Table(tables.Table):
        col = tables.EmailColumn()

    table = Table([{'col': 'test@example.com'}])
    assert table.rows[0].get_cell_value('col') == 'test@example.com'
