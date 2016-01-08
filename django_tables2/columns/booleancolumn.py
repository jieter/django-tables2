# coding: utf-8
from __future__ import absolute_import, unicode_literals

import six
from django.db import models
from django.utils.html import escape, format_html

from django_tables2.utils import AttributeDict

from .base import Column, library


@library.register
class BooleanColumn(Column):
    """
    A column suitable for rendering boolean data.

    :param  null: is `None` different from `False`?
    :type   null: `bool`
    :param yesno: text to display for True/False values, comma separated
    :type  yesno: iterable or string

    Rendered values are wrapped in a ``<span>`` to allow customisation by
    themes. By default the span is given the class ``true``, ``false``.

    In addition to *attrs* keys supported by `.Column`, the following are
    available:

    - *span* -- adds attributes to the <span> tag
    """
    def __init__(self, null=False, yesno="✔,✘", **kwargs):
        self.yesno = (yesno.split(',') if isinstance(yesno, six.string_types)
                      else tuple(yesno))
        if null:
            kwargs["empty_values"] = ()
        super(BooleanColumn, self).__init__(**kwargs)

    def render(self, value):
        value = bool(value)
        text = self.yesno[int(not value)]
        attrs = {"class": six.text_type(value).lower()}
        attrs.update(self.attrs.get("span", {}))

        return format_html(
            '<span {}>{}</span>',
            AttributeDict(attrs).as_html(),
            escape(text)
        )

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.BooleanField):
            return cls(verbose_name=field.verbose_name, null=False)
        if isinstance(field, models.NullBooleanField):
            return cls(verbose_name=field.verbose_name, null=True)
