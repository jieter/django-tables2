from typing import TYPE_CHECKING, Optional

from django.db import models

from .base import library
from .templatecolumn import TemplateColumn

if TYPE_CHECKING:
    from django.db.models.fields import Field


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

    def __init__(self, format: Optional[str] = None, short: bool = True, *args, **kwargs):
        if format is None:
            format = "SHORT_DATETIME_FORMAT" if short else "DATETIME_FORMAT"
        kwargs["template_code"] = '{{ value|date:"%s"|default:default }}' % format
        super().__init__(*args, **kwargs)

    @classmethod
    def from_field(cls, field: "Field", **kwargs) -> "Optional[DateTimeColumn]":
        if isinstance(field, models.DateTimeField):
            return cls(**kwargs)
        return None
