# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.template import Context, Template
from django.template.loader import get_template

from .base import Column, library


@library.register
class TemplateColumn(Column):
    '''
    A subclass of `.Column` that renders some template code to use as
    the cell value.

    Arguments:
        template_code (str): template code to render
        template_name (str): name of the template to render

    A `~django.template.Template` object is created from the
    *template_code* or *template_name* and rendered with a context containing:

    - *record*  -- data record for the current row
    - *value*   -- value from `record` that corresponds to the current column
    - *default* -- appropriate default value to use as fallback

    Example:

    .. code-block:: python

        class ExampleTable(tables.Table):
            foo = tables.TemplateColumn('{{ record.bar }}')
            # contents of `myapp/bar_column.html` is `{{ value }}`
            bar = tables.TemplateColumn(template_name='myapp/name2_column.html')

    Both columns will have the same output.
    '''
    empty_values = ()

    def __init__(self, template_code=None, template_name=None, **extra):
        super(TemplateColumn, self).__init__(**extra)
        self.template_code = template_code
        self.template_name = template_name

        if not self.template_code and not self.template_name:
            raise ValueError('A template must be provided')

    def render(self, record, table, value, bound_column, **kwargs):
        # If the table is being rendered using `render_table`, it hackily
        # attaches the context to the table as a gift to `TemplateColumn`.
        context = getattr(table, 'context', Context())
        context.update({
            'default': bound_column.default,
            'column': bound_column,
            'record': record,
            'value': value
        })

        try:
            if self.template_code:
                return Template(self.template_code).render(context)
            else:
                return get_template(self.template_name).render(context.flatten())
        finally:
            context.pop()
