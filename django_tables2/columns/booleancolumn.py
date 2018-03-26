# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db import models
from django.utils import six
from django.utils.html import escape, format_html

from django_tables2.templatetags.django_tables2 import title
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

    In addition to *attrs* keys supported by `~.Column`, the following are
    available:

     - *span* -- adds attributes to the ``<span>`` tag
    '''
    def __init__(self, null=False, yesno='✔,✘', **kwargs):
        self.yesno = (yesno.split(',') if isinstance(yesno, six.string_types)
                      else tuple(yesno))
        if null:
            kwargs['empty_values'] = ()
        super(BooleanColumn, self).__init__(**kwargs)

    def _get_bool_value(self, record, value, bound_column):
        # If record is a model, we need to check if it has choices defined.
        if hasattr(record, '_meta'):
            field = bound_column.accessor.get_field(record)

            # If that's the case, we need to inverse lookup the value to convert
            # to a boolean we can use.
            if hasattr(field, 'choices') and field.choices is not None and len(field.choices) > 0:
                value = next(val for val, name in field.choices if name == value)

        value = bool(value)
        return value

    def render(self, value, record, bound_column):
        value = self._get_bool_value(record, value, bound_column)
        text = self.yesno[int(not value)]
        attrs = {'class': six.text_type(value).lower()}
        attrs.update(self.attrs.get('span', {}))

        return format_html(
            '<span {}>{}</span>',
            AttributeDict(attrs).as_html(),
            escape(text)
        )

    def value(self, record, value, bound_column):
        '''
        Returns the content for a specific cell similarly to `.render` however without any html content.
        '''
        value = self._get_bool_value(record, value, bound_column)
        return str(value)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.NullBooleanField):
            return cls(verbose_name=title(field.verbose_name), null=True)

        if isinstance(field, models.BooleanField):
            null = getattr(field, 'null', False)
            return cls(verbose_name=title(field.verbose_name), null=null)
