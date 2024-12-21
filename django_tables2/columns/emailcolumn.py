from typing import TYPE_CHECKING, Union

from django.db import models

from .base import library
from .linkcolumn import BaseLinkColumn

if TYPE_CHECKING:
    from django.db.models import Field


@library.register
class EmailColumn(BaseLinkColumn):
    """
    Render email addresses to `mailto:`-links.

    Arguments:
        attrs (dict): HTML attributes that are added to the rendered
                      ``<a href="...">...</a>`` tag.
        text: Either static text, or a callable. If set, this will be used to
              render the text inside link instead of the value.

    Example::

        # models.py
        class Person(models.Model):
            name = models.CharField(max_length=200)
            email =  models.EmailField()

        # tables.py
        class PeopleTable(tables.Table):
            name = tables.Column()
            email = tables.EmailColumn()

        # result
        # [...]<a href="mailto:email@example.com">email@example.com</a>
    """

    def get_url(self, value) -> str:
        return f"mailto:{value}"

    @classmethod
    def from_field(cls, field: "Field", **kwargs) -> "Union[EmailColumn, None]":
        if isinstance(field, models.EmailField):
            return cls(**kwargs)
        return None
