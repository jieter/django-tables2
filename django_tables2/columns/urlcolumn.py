# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.db import models
from .base import library
from .linkcolumn import BaseLinkColumn


@library.register
class URLColumn(BaseLinkColumn):
    """
    Renders URL values as hyperlinks.

    :param text: Either static text, or a callable. If set, this
                 value will be used to render the text inside link
                 instead of value (default)

    Example::

        >>> class CompaniesTable(tables.Table):
        ...     www = tables.URLColumn()
        ...
        >>> table = CompaniesTable([{"www": "http://google.com"}])
        >>> table.rows[0]["www"]
        u'<a href="http://google.com">http://google.com</a>'

        >>> class CompaniesTable(tables.Table):
        ...     www = tables.URLColumn(text='Google')
        ...
        >>> table = CompaniesTable([{"www": "http://google.com"}])
        >>> table.rows[0]["www"]
        u'<a href="http://google.com">Google</a>'

    Additional attributes for the ``<a>`` tag can be specified via
    ``attrs['a']``.

    """
    def __init__(self, text=None, *args, **kwargs):
        self.text = text
        super(URLColumn, self).__init__(*args, **kwargs)

    def render(self, value, record, bound_column):
        text = value
        if self.text:
            text = self.text
            if callable(text):
                text = text(record)
        return self.render_link(self.compose_url(record, bound_column), text=text)
        

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.URLField):
            return cls(verbose_name=field.verbose_name)
