from django.db import models
from django.utils.text import capfirst

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
        super().__init__(template_code=template, *args, **kwargs)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.TimeField):
            return cls(verbose_name=capfirst(field.verbose_name))
