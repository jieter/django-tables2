# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.utils.safestring import mark_safe

from django_tables2.utils import AttributeDict

from .base import Column, library

@library.register
class CheckBoxColumn(Column):
    """
    A subclass of `.Column` that renders as a checkbox form input.

    This column allows a user to *select* a set of rows. The selection
    information can then be used to apply some operation (e.g. "delete") onto
    the set of objects that correspond to the selected rows.

    The value that is extracted from the :term:`table data` for this column is
    used as the value for the checkbox, i.e. ``<input type="checkbox"
    value="..." />``

    This class implements some sensible defaults:

    - HTML input's ``name`` attribute is the :term:`column name` (can override
      via *attrs* argument).
    - *orderable* defaults to `False`.

    .. note::

        You'd expect that you could select multiple checkboxes in the rendered
        table and then *do something* with that. This functionality isn't
        implemented. If you want something to actually happen, you'll need to
        implement that yourself.

    In addition to *attrs* keys supported by `.Column`, the following are
    available:

    - *input*     -- ``<input>`` elements in both ``<td>`` and ``<th>``.
    - *th__input* -- Replaces *input* attrs in header cells.
    - *td__input* -- Replaces *input* attrs in body cells.

    .. attribute:: th__before_input

        Is added to add content before the header input element:
        ``'<th>'+th__before_input+'<input ...>``

        :type: `unicode`
    """
    def __init__(self, attrs=None, **extra):
        kwargs = {'orderable': False, 'attrs': attrs}
        kwargs.update(extra)
        self.th__before_input = kwargs.pop('th__before_input','')
        super(CheckBoxColumn, self).__init__(**kwargs)

    @property
    def header(self):
        default = {'type': 'checkbox'}
        general = self.attrs.get('input')
        specific = self.attrs.get('th__input')
        attrs = AttributeDict(default, **(specific or general or {}))
        return mark_safe(self.th__before_input+'<input %s/>' % attrs.as_html())

    def render(self, value, bound_column):  # pylint: disable=W0221
        default = {
            'type': 'checkbox',
            'name': bound_column.name,
            'value': value
        }
        general = self.attrs.get('input')
        specific = self.attrs.get('td__input')
        attrs = AttributeDict(default, **(specific or general or {}))
        return mark_safe('<input %s/>' % attrs.as_html())
