import json
from typing import TYPE_CHECKING, Any, Optional

from django.db.models import JSONField
from django.utils.html import format_html
from django.utils.safestring import SafeString

from ..utils import AttributeDict
from .base import library
from .linkcolumn import BaseLinkColumn

if TYPE_CHECKING:
    from django.db.models import Field

try:
    from django.contrib.postgres.fields import HStoreField
except ImportError:
    # psycopg is not available, cannot import from django.contrib.postgres.
    HStoreField = None  # type: ignore


@library.register
class JSONColumn(BaseLinkColumn):
    """
    Render the contents of `~django.contrib.postgres.fields.JSONField` or
    `~django.contrib.postgres.fields.HStoreField` as an indented string.

    .. versionadded :: 1.5.0

    Arguments:
        json_dumps_kwargs: kwargs passed to `json.dumps`, defaults to `{'indent': 2}`
        attrs (dict): In addition to *attrs* keys supported by `~.Column`, the
            following are available:

             - ``pre`` -- ``<pre>`` around the rendered JSON string in ``<td>`` elements.

    """

    def __init__(self, json_dumps_kwargs=None, **kwargs):
        self.json_dumps_kwargs = (
            json_dumps_kwargs if json_dumps_kwargs is not None else {"indent": 2}
        )

        super().__init__(**kwargs)

    def render(self, value: Any) -> SafeString:
        return format_html(
            "<pre {}>{}</pre>",
            AttributeDict(self.attrs.get("pre", {})).as_html(),
            json.dumps(value, **self.json_dumps_kwargs),
        )

    @classmethod
    def from_field(cls, field: "Field", **kwargs) -> "Optional[JSONColumn]":
        if isinstance(field, JSONField) or (
            HStoreField is not None and isinstance(field, HStoreField)
        ):
            return cls(**kwargs)
        return None
