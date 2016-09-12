# coding: utf-8
from __future__ import absolute_import, unicode_literals

import os

from django.db import models
from django.utils.html import format_html

from django_tables2.templatetags.django_tables2 import title
from django_tables2.utils import AttributeDict

from .base import library
from .linkcolumn import BaseLinkColumn


@library.register
class FileColumn(BaseLinkColumn):
    '''
    Attempts to render `.FieldFile` (or other storage backend `.File`) as a
    hyperlink.

    When the file is accessible via a URL, the file is rendered as a
    hyperlink. The `.basename` is used as the text::

        <a href="/media/path/to/receipt.pdf" title="path/to/receipt.pdf">receipt.pdf</a>

    When unable to determine the URL, a ``span`` is used instead::

        <span title="path/to/receipt.pdf">receipt.pdf</span>

    `.Column.attrs` keys ``a`` and ``span`` can be used to add additional attributes.

    Arguments:
        verify_exists (bool): attempt to determine if the file exists
            If *verify_exists*, the HTML class ``exists`` or ``missing`` is
            added to the element to indicate the integrity of the storage.
        text (str or callable): Either static text, or a callable. If set, this
            will be used to render the text inside the link instead of
            the file's basename (default)
    '''
    def __init__(self, verify_exists=True, **kwargs):
        self.verify_exists = verify_exists
        super(FileColumn, self).__init__(**kwargs)

    def text_value(self, record, value):
        if self.text is None:
            return os.path.basename(value.name)
        return super(FileColumn, self).text_value(record, value)

    def render(self, record, value):
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

        classes = [c for c in attrs.get('class', '').split(' ') if c]
        if exists is not None:
            classes.append('exists' if exists else 'missing')
        attrs['class'] = ' '.join(classes)

        if url:
            return self.render_link(url, record=record, value=value, attrs=attrs)
        else:
            return format_html(
                '<span {attrs}>{text}</span>',
                attrs=attrs.as_html(),
                text=self.text_value(record, value)
            )

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.FileField):
            return cls(verbose_name=title(field.verbose_name))
