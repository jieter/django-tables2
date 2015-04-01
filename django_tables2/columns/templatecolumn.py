# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.template import Context, Template
from django.template.loader import render_to_string
from .base import Column, library


@library.register
class TemplateColumn(Column):
    """
    A subclass of `.Column` that renders some template code to use as
    the cell value.

    :type  template_code: `unicode`
    :param template_code: the template code to render
    :type  template_name: `unicode`
    :param template_name: the name of the template to render

    A `~django.template.Template` object is created from the
    *template_code* or *template_name* and rendered with a context containing:

    - *record* -- data record for the current row
    - *column* -- name of the current column
    - *value* -- value from `record` that corresponds to `column`
    - *default* -- appropriate default value to use as fallback

    Example:

    .. code-block:: python

        class ExampleTable(tables.Table):
            foo = tables.TemplateColumn('{{ record.bar }}')
            # contents of `myapp/bar_column.html` is `{{ value }}`
            bar = tables.TemplateColumn(template_name='myapp/name2_column.html')

    Both columns will have the same output.

    .. important::

        In order to use template tags or filters that require a
        `~django.template.RequestContext`, the table **must** be rendered via
        :ref:`{% render_table %} <template-tags.render_table>`.
    """
    empty_values = ()

    def __init__(self, template_code=None, template_name=None, **extra):
        super(TemplateColumn, self).__init__(**extra)
        self.template_code = template_code
        self.template_name = template_name
        if not self.template_code and not self.template_name:
            raise ValueError('A template must be provided')

    def render(self, record, table, value, bound_column, **kwargs):
        # If the table is being rendered using `render_table`, it hackily
        # attaches the context to the table as a gift to `TemplateColumn`. If
        # the table is being rendered via `Table.as_html`, this won't exist.
        context = getattr(table, 'context', Context())
        context.update({'default': bound_column.default,
                        'column': bound_column.name,
                        'record': record, 'value': value})
        try:
            if self.template_code:
                return Template(self.template_code).render(context)
            else:
                return render_to_string(self.template_name, context)
        finally:
            context.pop()
