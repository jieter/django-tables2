# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db import models

from django_tables2.utils import ucfirst

from .base import library
from .templatecolumn import TemplateColumn


@library.register
class DateTimeColumn(TemplateColumn):
    """
    A column that renders `datetime` instances in the local timezone.

    Arguments:
        format (str): format string for datetime (optional).
                      Note that *format* uses Django's `date` template tag syntax.
        short (bool): if `format` is not specified, use Django's
                      ``SHORT_DATETIME_FORMAT``, else ``DATETIME_FORMAT``
    """

    def __init__(self, format=None, short=True, *args, **kwargs):
        if format is None:
            format = "SHORT_DATETIME_FORMAT" if short else "DATETIME_FORMAT"
        template = '{{ value|date:"%s"|default:default }}' % format
        super(DateTimeColumn, self).__init__(template_code=template, *args, **kwargs)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.DateTimeField):
            return cls(verbose_name=ucfirst(field.verbose_name))
