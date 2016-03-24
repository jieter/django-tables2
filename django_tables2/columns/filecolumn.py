# coding: utf-8
from __future__ import absolute_import, unicode_literals

import os

from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from django_tables2.utils import AttributeDict

from .base import Column, library


@library.register
class FileColumn(Column):
    """
    Attempts to render `.FieldFile` (or other storage backend `.File`) as a
    hyperlink.

    When the file is accessible via a URL, the file is rendered as a
    hyperlink. The `.basename` is used as the text::

        <a href="/media/path/to/receipt.pdf" title="path/to/receipt.pdf">receipt.pdf</a>

    When unable to determine the URL, a ``span`` is used instead::

        <span title="path/to/receipt.pdf">receipt.pdf</span>

    `.Column.attrs` keys ``a`` and ``span`` can be used to add additional attributes.

    :type  verify_exists: bool
    :param verify_exists: attempt to determine if the file exists

    If *verify_exists*, the HTML class ``exists`` or ``missing`` is added to
    the element to indicate the integrity of the storage.
    """
    def __init__(self, verify_exists=True, **kwargs):
        self.verify_exists = True
        super(FileColumn, self).__init__(**kwargs)

    def render(self, value):
        storage = getattr(value, 'storage', None)
        exists = None
        url = None
        if storage:
            # we'll assume value is a `django.db.models.fields.files.FieldFile`
            if self.verify_exists:
                exists = storage.exists(value.name)
            url = storage.url(value.name)

        else:
            if self.verify_exists and hasattr(value, 'name'):
                # ignore negatives, perhaps the file has a name but it doesn't
                # represent a local path... better to stay neutral than give a
                # false negative.
                exists = os.path.exists(value.name) or exists

        tag = 'a' if url else 'span'
        attrs = AttributeDict(self.attrs.get(tag, {}))
        attrs['title'] = value.name
        if url:
            attrs['href'] = url

        classes = [c for c in attrs.get('class', '').split(' ') if c]
        if exists is not None:
            classes.append('exists' if exists else 'missing')
        attrs['class'] = ' '.join(classes)

        return format_html(
            '<{tag} {attrs}>{text}</{tag}>',
            tag=tag,
            attrs=attrs.as_html(),
            text=os.path.basename(value.name)
        )

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.FileField):
            return cls(verbose_name=field.verbose_name)
