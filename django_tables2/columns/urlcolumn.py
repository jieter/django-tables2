# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db import models

from django_tables2.templatetags.django_tables2 import title

from .base import library
from .linkcolumn import BaseLinkColumn


@library.register
class URLColumn(BaseLinkColumn):
    '''
    Renders URL values as hyperlinks.

    Arguments:
        text (str or callable): Either static text, or a callable. If set, this
            will be used to render the text inside link instead of value (default)
        attrs (dict): Additional attributes for the ``<a>`` tag

    Example::

        >>> class CompaniesTable(tables.Table):
        ...     www = tables.URLColumn()
        ...
        >>> table = CompaniesTable([{'www': 'http://google.com'}])
        >>> table.rows[0].get_cell('www')
        '<a href="http://google.com">http://google.com</a>'
    '''
    def render(self, record, value):
        return self.render_link(value, record=record, value=value)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.URLField):
            return cls(verbose_name=title(field.verbose_name))
