# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db import models

from django_tables2.utils import ucfirst

from .base import library
from .templatecolumn import TemplateColumn


@library.register
class DateColumn(TemplateColumn):
    '''
    A column that renders dates in the local timezone.

    Arguments:
        format (str): format string in same format as Django's ``date`` template
                      filter (optional)
        short (bool): if `format` is not specified, use Django's
                      ``SHORT_DATE_FORMAT`` setting, otherwise use ``DATE_FORMAT``
    '''
    def __init__(self, format=None, short=True, *args, **kwargs):
        if format is None:
            format = 'SHORT_DATE_FORMAT' if short else 'DATE_FORMAT'
        template = '{{ value|date:"%s"|default:default }}' % format
        super(DateColumn, self).__init__(template_code=template, *args, **kwargs)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.DateField):
            return cls(verbose_name=ucfirst(field.verbose_name))
