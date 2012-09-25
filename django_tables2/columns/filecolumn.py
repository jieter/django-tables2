# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django_tables2.utils import A, AttributeDict
import os
import warnings
from .base import Column, library


@library.register
class FileColumn(Column):
    """
    Renders a FieldFile (or other storage backend File) as a link.

    In addition to ``attrs`` keys supported by ``Column``, the following are
    available:

    :type  verify_exists: bool
    :param verify_exists: *try* to determine if the file actually exists.

    - *a* -- ``<a>`` elements in ``<td>``
    - *span* -- ``<span>`` elements in ``<td>`` (missing files)

    if *verify_exists*, the HTML class ``exists`` or ``missing`` is added to
    the element.
    """
    def __init__(self, verify_exists=True, **kwargs):
        self.verify_exists = True
        super(FileColumn, self).__init__(**kwargs)

    def render(self, value):
        storage = getattr(value, "storage", None)
        exists = None
        url = None
        if storage:
            # we'll assume value is a `django.db.models.fields.files.FieldFile`
            fieldfile = value
            if self.verify_exists:
                exists = storage.exists(value.name)
            url = storage.url(value.name)

        else:
            if self.verify_exists and hasattr(value, "name"):
                # ignore negatives, perhaps the file has a name but it doesn't
                # represent a local path... better to stay neutral than give a
                # false negative.
                exists = os.path.exists(value.name) or exists

        tag = 'a' if url else 'span'
        attrs = AttributeDict(self.attrs.get(tag, {}))
        attrs['title'] = value.name
        if url:
            attrs['href'] = url

        # add "exists" or "missing" to the class list
        classes = [c for c in attrs.get('class', '').split(' ') if c]
        if exists is True:
            classes.append("exists")
        elif exists is False:
            classes.append("missing")
        attrs['class'] = " ".join(classes)

        html ='<{tag} {attrs}>{text}</{tag}>'.format(
            tag=tag,
            attrs=attrs.as_html(),
            text=os.path.basename(value.name))
        return mark_safe(html)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.FileField):
            return cls(verbose_name=field.verbose_name)
