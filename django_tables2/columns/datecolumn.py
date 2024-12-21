from typing import TYPE_CHECKING, Union

from django.db import models

from .base import library
from .templatecolumn import TemplateColumn

if TYPE_CHECKING:
    from django.db.models import Field


@library.register
class DateColumn(TemplateColumn):
    """
    A column that renders dates in the local timezone.

    Arguments:
        format (str): format string in same format as Django's ``date`` template
                      filter (optional)
        short (bool): if `format` is not specified, use Django's
                      ``SHORT_DATE_FORMAT`` setting, otherwise use ``DATE_FORMAT``
    """

    def __init__(self, format: Union[str, None] = None, short: bool = True, *args, **kwargs):
        if format is None:
            format = "SHORT_DATE_FORMAT" if short else "DATE_FORMAT"
        kwargs["template_code"] = '{{ value|date:"%s"|default:default }}' % format
        super().__init__(*args, **kwargs)

    @classmethod
    def from_field(cls, field: "Field", **kwargs) -> "Union[DateColumn, None]":
        if isinstance(field, models.DateField):
            return cls(**kwargs)
        return None
