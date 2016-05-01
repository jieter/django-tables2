# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.db import models

from .base import library
from .linkcolumn import BaseLinkColumn


@library.register
class EmailColumn(BaseLinkColumn):
    """
    A subclass of `.BaseLinkColumn` that renders the cell value as a hyperlink.

    It's common to have a email value in a row hyperlinked to another page.

    :param  attrs: a `dict` of HTML attributes that are added to the rendered
                   ``<a href="...">...</a>`` tag
    :param   text: Either static text, or a callable. If set, this value will be
                   used to render the text inside link instead of value (default)

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
    def render(self, record, value):
        return self.render_link(
            uri='mailto:{}'.format(value),
            record=record,
            value=value
        )

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.EmailField):
            return cls(verbose_name=field.verbose_name)
