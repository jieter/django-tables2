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

        >>> class CompaniesTable(tables.Table):
        ...     www = tables.URLColumn(label='Google')
        ...
        >>> table = CompaniesTable([{"www": "http://google.com"}])
        >>> table.rows[0]["www"]
        u'<a href="http://google.com">Google</a>'

    Additional attributes for the ``<a>`` tag can be specified via
    ``attrs['a']``.

    """
    def __init__(self, *args, **kwargs):
        self.label = kwargs.pop('label', False)
        super(URLColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        if self.label:
            label = self.label
        else:
            label = value
        return self.render_link(value, label)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.URLField):
            return cls(verbose_name=field.verbose_name)
