# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.db import models
from .base import library
from .linkcolumn import BaseLinkColumn


@library.register
class URLColumn(BaseLinkColumn):
    """
    A subclass of :class:`.BaseLinkColumn` that renders the cell value as a hyperlink.

    It's common to have a URL value in a row hyperlinked to other page.

    :param  attrs: a :class:`dict` of HTML attributes that are added to
                   the rendered ``<a href="...">...</a>`` tag

    Example:

    .. code-block:: python

        # models.py
        class Person(models.Model):
            name = models.CharField(max_length=200)
            web =  models.URLField()

        # tables.py
        class PeopleTable(tables.Table):
            name = tables.Column()
            web = tables.URLColumn()

    """
    def render(self, value):
        return self.render_link(value, value)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.URLField):
            return cls(verbose_name=field.verbose_name)
