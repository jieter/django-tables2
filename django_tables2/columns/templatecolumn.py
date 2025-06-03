from django.template import Context, Template
from django.template.loader import get_template
from django.utils.html import strip_tags

from ..utils import call_with_appropriate
from .base import Column, library


@library.register
class TemplateColumn(Column):
    """
    A subclass of `.Column` that renders some template code to use as the cell value.

    Arguments:
        template_code (str): template code to render
        template_name (str): name of the template to render
        context_object_name (str): name of the context variable to pas the record in, defaults to "record".
        extra_context (dict): optional extra template context. If a callable is passed, it will be called with
            optional record, table, value, bound_column arguments.

    A `~django.template.Template` object is created from the
    *template_code* or *template_name* and rendered with a context containing:

    - *record*      -- data record for the current row
    - *value*       -- value from `record` that corresponds to the current column
    - *default*     -- appropriate default value to use as fallback.
    - *row_counter* -- The number of the row this cell is being rendered in.
    - any context variables passed using the `extra_context` argument to `TemplateColumn`.

    Example:

    .. code-block:: python

        class ExampleTable(tables.Table):
            foo = tables.TemplateColumn("{{ record.bar }}")
            # contents of `myapp/bar_column.html` is `{{ label }}: {{ value }}`
            bar = tables.TemplateColumn(template_name="myapp/name2_column.html",
                                        extra_context={"label": "Label"})

    Both columns will have the same output.
    """

    empty_values = ()

    def __init__(
        self,
        template_code=None,
        template_name=None,
        context_object_name="record",
        extra_context=None,
        **extra
    ):
        super().__init__(**extra)
        self.template_code = template_code
        self.template_name = template_name
        self.extra_context = extra_context or {}
        self.context_object_name = context_object_name

        if not self.template_code and not self.template_name:
            raise ValueError("A template must be provided")

    def render(self, record, table, value, bound_column, **kwargs):
        # If the table is being rendered using `render_table`, it hackily
        # attaches the context to the table as a gift to `TemplateColumn`.
        context = getattr(table, "context", Context())
        additional_context = {
            "default": bound_column.default,
            "column": bound_column,
            self.context_object_name: record,
            "value": value,
            "row_counter": kwargs["bound_row"].row_counter,
        }

        extra_context = self.extra_context
        if callable(extra_context):
            extra_context = call_with_appropriate(
                extra_context,
                {"record": record, "table": table, "value": value, "bound_column": bound_column},
            )
        additional_context.update(extra_context)
        with context.update(additional_context):
            if self.template_code:
                return Template(self.template_code).render(context)
            else:
                return get_template(self.template_name).render(context.flatten())

    def value(self, **kwargs):
        """
        Non-HTML value returned from a call to `value()` on a `TemplateColumn`.

        By default this is the rendered template with `django.utils.html.strip_tags` applied.
        Leading and trailing whitespace is stripped.
        """
        html = super().value(**kwargs)
        return strip_tags(html).strip() if isinstance(html, str) else html
