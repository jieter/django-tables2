# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db import models

from django_tables2.utils import ucfirst

from .base import library
from .templatecolumn import TemplateColumn


@library.register
class TimeColumn(TemplateColumn):
    """
    A column that renders times in the local timezone.

    Arguments:
        format (str): format string in same format as Django's ``time`` template
            filter (optional)
        short (bool): if *format* is not specified, use Django's ``TIME_FORMAT``
            setting
    """

    def __init__(self, format=None, *args, **kwargs):
        if format is None:
            format = "TIME_FORMAT"
        template = '{{ value|date:"%s"|default:default }}' % format
        super(TimeColumn, self).__init__(template_code=template, *args, **kwargs)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.TimeField):
            return cls(verbose_name=ucfirst(field.verbose_name))
