# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils import six
from django.utils.html import escape, format_html

from django_tables2.utils import AttributeDict

from .base import Column, library


@library.register
class BooleanColumn(Column):
    '''
    A column suitable for rendering boolean data.

    Arguments:
        null (bool): is `None` different from `False`?
        yesno (str): text to display for True/False values, comma separated

    Rendered values are wrapped in a ``<span>`` to allow customisation by
    themes. By default the span is given the class ``true``, ``false``.

    In addition to *attrs* keys supported by `.Column`, the following are
    available:

    - *span* -- adds attributes to the <span> tag
    '''
    def __init__(self, null=False, yesno='✔,✘', **kwargs):
        self.yesno = (yesno.split(',') if isinstance(yesno, six.string_types)
                      else tuple(yesno))
        if null:
            kwargs['empty_values'] = ()
        super(BooleanColumn, self).__init__(**kwargs)

    def render(self, value, record, bound_column):
        # if record is a model, we need to check if it has choices defined.
        # If that's the case, we need to inverse lookup the value to convert to
        # a boolean.
        if hasattr(record, '_meta'):
            field = bound_column.accessor.get_field(record)
            if hasattr(field, 'choices') and field.choices is not None:
                value = next(val for val, name in field.choices if name == value)

        value = bool(value)
        text = self.yesno[int(not value)]
        attrs = {'class': six.text_type(value).lower()}
        attrs.update(self.attrs.get('span', {}))

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
