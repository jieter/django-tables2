from typing import TYPE_CHECKING, Any

from django.template import Context, Template
from django.template.loader import get_template
from django.utils.html import strip_tags
from django.utils.safestring import SafeString

from django_tables2.rows import BoundRow

from .base import BoundColumn, CellArguments, Column, library

if TYPE_CHECKING:
    from typing_extensions import Unpack


@library.register
class TemplateColumn(Column):
    """
    A subclass of `.Column` that renders some template code to use as the cell value.

    Arguments:
        template_code (str): template code to render
        template_name (str): name of the template to render
        extra_context (dict): optional extra template context

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
        template_code: str | None = None,
        template_name: str | None = None,
        extra_context: dict | None = None,
        **extra,
    ):
        super().__init__(**extra)
        self.template_code = template_code
        self.template_name = template_name
        self.extra_context = extra_context or {}

        if not self.template_code and not self.template_name:
            raise ValueError("A template must be provided")

    def render(self, **kwargs: "Unpack[CellArguments]") -> "SafeString":
        # If the table is being rendered using `render_table`, it hackily
        # attaches the context to the table as a gift to `TemplateColumn`.
        table = kwargs["table"]
        context = getattr(table, "context", Context())
        bound_column: BoundColumn = kwargs["bound_column"]
        bound_row: BoundRow = kwargs["bound_row"]
        additional_context = {
            "default": bound_column.default,
            "column": bound_column,
            "record": kwargs["record"],
            "value": kwargs["value"],
            "row_counter": bound_row.row_counter,
        }
        additional_context.update(self.extra_context)
        with context.update(additional_context):
            if self.template_code:
                return Template(self.template_code).render(context)
            elif self.template_name:
                dict_context: dict[Any, Any] = context.flatten()
                return SafeString(get_template(self.template_name).render(dict_context))
        return SafeString("")

    def value(self, **kwargs) -> Any:
        """
        Non-HTML value returned from a call to `value()` on a `TemplateColumn`.

        By default this is the rendered template with `django.utils.html.strip_tags` applied.
        Leading and trailing whitespace is stripped.
        """
        html = super().value(**kwargs)
        return strip_tags(html).strip() if isinstance(html, str) else html
