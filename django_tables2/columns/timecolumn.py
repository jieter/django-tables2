from typing import TYPE_CHECKING, Union

from django.db import models

from .base import library
from .templatecolumn import TemplateColumn

if TYPE_CHECKING:
    from django.db.models import Field


@library.register
class TimeColumn(TemplateColumn):
    """
    A column that renders times in the local timezone.

    Arguments:
        format (str): format string in same format as Django's ``time`` template filter (optional).
        short (bool): if *format* is not specified, use Django's ``TIME_FORMAT`` setting.
    """

    def __init__(self, format: Union[str, None] = None, *args, **kwargs):
        if format is None:
            format = "TIME_FORMAT"
        kwargs["template_code"] = '{{ value|date:"%s"|default:default }}' % format
        super().__init__(*args, **kwargs)

    @classmethod
    def from_field(cls, field: "Field", **kwargs) -> "Union[TimeColumn, None]":
        if isinstance(field, models.TimeField):
            return cls(**kwargs)
        return None
