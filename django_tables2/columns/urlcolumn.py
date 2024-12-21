from typing import TYPE_CHECKING, Optional

from django.db import models

from .base import library
from .linkcolumn import BaseLinkColumn

if TYPE_CHECKING:
    from django.db.models.fields import Field


@library.register
class URLColumn(BaseLinkColumn):
    """
    Renders URL values as hyperlinks.

    Arguments:
        text (str or callable): Either static text, or a callable. If set, this
            will be used to render the text inside link instead of value (default)
        attrs (dict): Additional attributes for the ``<a>`` tag

    Example::

        >>> class CompaniesTable(tables.Table):
        ...     link = tables.URLColumn()
        ...
        >>> table = CompaniesTable([{"link": "http://google.com"}])
        >>> table.rows[0].get_cell("link")
        '<a href="http://google.com">http://google.com</a>'
    """

    def get_url(self, value: str) -> str:
        return value

    @classmethod
    def from_field(cls, field: "Field", **kwargs) -> "Optional[URLColumn]":
        if isinstance(field, models.URLField):
            return cls(**kwargs)
        return None
