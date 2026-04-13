from collections.abc import Callable

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
        context_object_name (str): name of the context variable that represents the record, defaults to "record".
        extra_context (dict | callable): optional extra template context. Any callables passed will be called with the following
            optional arguments: record, table, value, and bound_column.

    A `~django.template.Template` object is created from the
    *template_code* or *template_name* and rendered with a context containing:

    - *record*      -- Data record for the current row.
    - *value*       -- Value from `record` that corresponds to the current column.
    - *default*     -- Appropriate default value to use as fallback.
    - *row_counter* -- The number of the row this cell is being rendered in.
    - *request*.    -- If the table configured using ``RequestConfig(request).configure(table)``.
    - any context variables passed using the ``extra_context`` argument to `TemplateColumn`.

    Example:

    .. code-block:: python

        class ExampleTable(tables.Table):
            foo = tables.TemplateColumn("{{ record.bar }}")
            # contents of `myapp/bar_column.html` is `{{ label }}: {{ value }}`
            bar = tables.TemplateColumn(template_name="myapp/name2_column.html",
                                        extra_context={"label": "Label"})

    Both columns will have the same output.

    If you need more complex extra context, you can override the `get_context_data` method instead of passing
    `extra_context`.

    .. code-block:: python

        class PriorityColumn(TemplateColumn):
            template_name = "priority_column.html"
            def get_context_data(self, record, **kwargs):
                context = super().get_context_data(record=record, **kwargs)
                context["overdue"] = record.due_date < date.today()
                return context
    """

    empty_values = ()

    def __init__(
        self,
        template_code: str | None = None,
        template_name: str | None = None,
        context_object_name: str | None = None,
        extra_context: dict | Callable[..., dict] | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.template_code = template_code or getattr(self, "template_code", None)
        self.template_name = template_name or getattr(self, "template_name", None)
        self.extra_context = extra_context or {}
        self.context_object_name = context_object_name or getattr(
            self, "context_object_name", "record"
        )

        if not getattr(self, "template_code", None) and not getattr(self, "template_name", None):
            raise ValueError("A template must be provided")

    def get_context_data(self, *, record, table, value, bound_column, **kwargs):
        """
        Generate the context data for rendering the template column template.

        This context will be added to the parent template context if available.
        """
        context = {
            "default": bound_column.default,
            "column": bound_column,
            self.context_object_name: record,
            "value": value,
            "row_counter": kwargs["bound_row"].row_counter,
        }

        extra_context = self.extra_context
        if callable(extra_context):
            optional_kwargs = {
                "record": record,
                "table": table,
                "value": value,
                "bound_column": bound_column,
            }
            extra_context = call_with_appropriate(extra_context, optional_kwargs)
        return context | extra_context

    def render(self, record, table, value, bound_column, **kwargs):
        # If the table is being rendered using `render_table`, it hackily
        # attaches the context to the table as a gift to `TemplateColumn`.
        parent_context = getattr(table, "context", Context())

        context = self.get_context_data(
            record=record, table=table, value=value, bound_column=bound_column, **kwargs
        )
        with parent_context.update(context):
            request = getattr(table, "request", None)
            if self.template_code:
                parent_context["request"] = request
                return Template(self.template_code).render(parent_context)
            else:
                return get_template(self.template_name).render(
                    parent_context.flatten(), request=request
                )

    def value(self, **kwargs):
        """
        Non-HTML value returned from a call to `value()` on a `TemplateColumn`.

        By default this is the rendered template with `django.utils.html.strip_tags` applied.
        Leading and trailing whitespace is stripped.
        """
        html = super().value(**kwargs)
        return strip_tags(html).strip() if isinstance(html, str) else html
