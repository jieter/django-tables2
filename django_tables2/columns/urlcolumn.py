# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.db import models
from .base import library
from .linkcolumn import BaseLinkColumn


@library.register
class URLColumn(BaseLinkColumn):
    """
    Renders URL values as hyperlinks.

    Example::

        >>> class CompaniesTable(tables.Table):
        ...     www = tables.URLColumn()
        ...
        >>> table = CompaniesTable([{"www": "http://google.com"}])
        >>> table.rows[0]["www"]
        u'<a href="http://google.com">http://google.com</a>'

    Additional attributes for the ``<a>`` tag can be specified via
    ``attrs['a']``.

    """
    def render(self, value):
        return self.render_link(value, value)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.URLField):
            return cls(verbose_name=field.verbose_name)
