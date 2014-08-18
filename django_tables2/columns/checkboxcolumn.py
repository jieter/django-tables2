# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.utils.safestring import mark_safe
from django_tables2.utils import AttributeDict, A
import warnings
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
    
    Use :term:`checked` to mark a column as the 'checkable' column for data set.
    If `checked` is a non-falsey value, the checkbox will render checked.
    """
    def __init__(self, attrs=None, checked=None, **extra):
        self.checked = A(checked) if checked else None
        # For backwards compatibility, passing in a normal dict effectively
        # should assign attributes to the `<input>` tag.
        valid = set(("input", "th__input", "td__input", "th", "td", "cell"))
        if attrs and not set(attrs) & set(valid):
            # if none of the keys in attrs are actually valid, assume it's some
            # old code that should be be interpreted as {"td__input": ...}
            warnings.warn('attrs keys must be one of %s, interpreting as {"td__input": %s}'
                          % (', '.join(valid), attrs), DeprecationWarning)
            attrs = {"td__input": attrs}
        # This is done for backwards compatible too, there used to be a
        # ``header_attrs`` argument, but this has been deprecated. We'll
        # maintain it for a while by translating it into ``head.checkbox``.
        if "header_attrs" in extra:
            warnings.warn('header_attrs argument is deprecated, '
                          'use attrs={"th__input": ...} instead',
                          DeprecationWarning)
            attrs.setdefault('th__input', {}).update(extra.pop('header_attrs'))

        kwargs = {'orderable': False, 'attrs': attrs}
        kwargs.update(extra)
        super(CheckBoxColumn, self).__init__(**kwargs)

    @property
    def header(self):
        default = {'type': 'checkbox'}
        general = self.attrs.get('input')
        specific = self.attrs.get('th__input')
        attrs = AttributeDict(default, **(specific or general or {}))
        return mark_safe('<input %s/>' % attrs.as_html())

    def render(self, value, bound_column, record):  # pylint: disable=W0221
        default = {
            'type': 'checkbox',
            'name': bound_column.name,
            'value': value
        }
        if self.checked and getattr(record, self.checked, False):
            default.update({
                'checked': 'checked',
            })
        general = self.attrs.get('input')
        specific = self.attrs.get('td__input')
        attrs = AttributeDict(default, **(specific or general or {}))
        return mark_safe('<input %s/>' % attrs.as_html())
