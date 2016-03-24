# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db import models

from .base import library
from .linkcolumn import BaseLinkColumn


@library.register
class EmailColumn(BaseLinkColumn):
    """
    A subclass of `.BaseLinkColumn` that renders the cell value as a hyperlink.

    It's common to have a email value in a row hyperlinked to other page.

    :param  attrs: a `dict` of HTML attributes that are added to
                   the rendered ``<a href="...">...</a>`` tag

    Example:

    .. code-block:: python

        # models.py
        class Person(models.Model):
            name = models.CharField(max_length=200)
            email =  models.EmailField()

        # tables.py
        class PeopleTable(tables.Table):
            name = tables.Column()
            email = tables.EmailColumn()

    """
    def render(self, value):
        return self.render_link('mailto:%s' % value, text=value)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.EmailField):
            return cls(verbose_name=field.verbose_name)
