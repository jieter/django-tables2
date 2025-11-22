from typing import TYPE_CHECKING, Any

from django.db import models
from django.utils.html import escape, format_html

from ..utils import AttributeDict
from .base import BoundColumn, CellArguments, Column, library

if TYPE_CHECKING:
    from django.db.models import Field
    from django.utils.safestring import SafeString
    from typing_extensions import Unpack


@library.register
class BooleanColumn(Column):
    """
    A column suitable for rendering boolean data.

    Arguments:
        null (bool): is `None` different from `False`?
        yesno (str): comma separated values string or 2-tuple to display for
                     True/False values.

    Rendered values are wrapped in a ``<span>`` to allow customization by using CSS.
    By default the span is given the class ``true``, ``false``.

    In addition to *attrs* keys supported by `~.Column`, the following are available:

     - ``span`` -- adds attributes to the ``<span>`` tag
    """

    def __init__(self, null: bool = False, yesno: str = "✔,✘", **kwargs):
        self.yesno = yesno.split(",") if isinstance(yesno, str) else tuple(yesno)
        if not null:
            kwargs["empty_values"] = ()
        super().__init__(**kwargs)

    def _get_bool_value(self, record: Any, value: Any, bound_column: BoundColumn) -> bool:
        # If record is a model, we need to check if it has choices defined.
        if hasattr(record, "_meta"):
            field = bound_column.accessor.get_field(record)

            # If that's the case, we need to inverse lookup the value to convert
            # to a boolean we can use.
            choices = getattr(field, "choices", None)
            if choices is not None and len(choices) > 0:
                value = next(val for val, name in choices if name == value)

        return bool(value)

    def render(self, **kwargs: "Unpack[CellArguments]") -> "SafeString":
        value = self._get_bool_value(kwargs["record"], kwargs["value"], kwargs["bound_column"])
        text = self.yesno[int(not value)]
        attrs = {"class": str(value).lower()}
        attrs.update(self.attrs.get("span", {}))

        return format_html("<span {}>{}</span>", AttributeDict(attrs).as_html(), escape(text))

    def value(self, **kwargs: "Unpack[CellArguments]") -> Any:
        """Return the content for a specific cell similarly to `.render` however without any html content."""
        return str(self._get_bool_value(kwargs["record"], kwargs["value"], kwargs["bound_column"]))

    @classmethod
    def from_field(cls, field: "Field", **kwargs) -> "BooleanColumn | None":
        if isinstance(field, models.BooleanField):
            return cls(null=getattr(field, "null", False), **kwargs)

        return None
