# coding: utf-8
from __future__ import absolute_import, unicode_literals
from collections import defaultdict
from django.core.urlresolvers import reverse
from django.db.models.fields import FieldDoesNotExist
from django.db import models
from django.template import Context, Template
from django.template.loader import render_to_string
from django.utils.datastructures import SortedDict
from django.utils.functional import curry
from django.utils.html import escape
from django.utils.safestring import mark_safe, SafeData
from itertools import ifilter, islice
import warnings
import inspect
from .templatetags.django_tables2 import title
from .utils import A, AttributeDict, OrderBy, OrderByTuple


funcs = ifilter(curry(hasattr, inspect), ('getfullargspec', 'getargspec'))
getargspec = getattr(inspect, next(funcs))
del funcs


class Library(object):
    """
    A collection of columns.
    """
    def __init__(self):
        self.columns = []

    def register(self, column):
        self.columns.append(column)
        return column

    def column_for_field(self, field):
        """
        Return a column object suitable for model field.

        :returns: column object of ``None``
        """
        # iterate in reverse order as columns are registered in order
        # of least to most specialised (i.e. Column is registered
        # first). This also allows user-registered columns to be
        # favoured.
        for candidate in reversed(self.columns):
            if not hasattr(candidate, "from_field"):
                continue
            column = candidate.from_field(field)
            if column is None:
                continue
            return column


# The library is a mechanism for announcing what columns are available. Its
# current use is to allow the table metaclass to ask columns if they're a
# suitable match for a model field, and if so to return an approach instance.
library = Library()


@library.register
class Column(object):  # pylint: disable=R0902
    """
    Represents a single column of a table.

    :class:`Column` objects control the way a column (including the cells that
    fall within it) are rendered.

    :param verbose_name: A human readable version of the column name. This
                         should not be title case. It is converted to title
                         case for use in column headers.
    :type  verbose_name: ``unicode``
    :type      accessor: :class:`basestring` or :class:`~.utils.Accessor`
    :param     accessor: An accessor that describes how to extract values for
                         this column from the :term:`table data`.
    :param      default: The default value for the column. This can be a value
                         or a callable object [1]_. If an object in the data
                         provides :const:`None` for a column, the default will
                         be used instead.

                         The default value may affect ordering, depending on
                         the type of data the table is using. The only case
                         where ordering is not affected is when a
                         :class:`QuerySet` is used as the table data (since
                         sorting is performed by the database).

                         .. [1] The provided callable object must not expect to
                                receive any arguments.
    :param    order_by: Allows one or more accessors to be used for ordering
                        rather than ``accessor``.
    :type     order_by: :class:`unicode`, :class:`tuple`, :class:`~utils.Accessor`
    :type      visible: :class:`bool`
    :param     visible: If :const:`False`, this column will not be in HTML from
                        output generators (e.g. :meth:`as_html` or
                        ``{% render_table %}``).

                        When a field is not visible, it is removed from the
                        table's :attr:`~Column.columns` iterable.
    :type    orderable: :class:`bool`
    :param   orderable: If :const:`False`, this column will not be allowed to
                        influence row ordering/sorting.
    :type        attrs: :class:`dict` object
    :param       attrs: HTML attributes to be added to components in the column

    Supported ``attrs`` keys are:

    - *th* -- ``<th>`` element in header
    - *td* -- ``<td>`` element in body
    - *cell* -- fall back for ``<th>`` and ``<td>`` should they not be specified
    """
    #: Tracks each time a Column instance is created. Used to retain order.
    creation_counter = 0
    empty_values = (None, '')

    def __init__(self, verbose_name=None, accessor=None, default=None,
                 visible=True, orderable=None, attrs=None, order_by=None,
                 sortable=None, empty_values=None):
        if not (accessor is None or isinstance(accessor, basestring) or
                callable(accessor)):
            raise TypeError('accessor must be a string or callable, not %s' %
                            type(accessor).__name__)
        if callable(accessor) and default is not None:
            raise TypeError('accessor must be string when default is used, not callable')
        self.accessor = A(accessor) if accessor else None
        self._default = default
        self.verbose_name = verbose_name
        self.visible = visible
        if sortable is not None:
            warnings.warn('`sortable` is deprecated, use `orderable` instead.',
                          DeprecationWarning)
            # if orderable hasn't been specified, we'll use sortable's value
            if orderable is None:
                orderable = sortable
        self.orderable = orderable
        self.attrs = attrs or {}
        # massage order_by into an OrderByTuple or None
        order_by = (order_by, ) if isinstance(order_by, basestring) else order_by
        self.order_by = OrderByTuple(order_by) if order_by is not None else None
        if empty_values is not None:
            self.empty_values = empty_values

        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

    @property
    def default(self):
        # handle callables
        return self._default() if callable(self._default) else self._default

    @property
    def header(self):
        """
        The value used for the column heading (e.g. inside the ``<th>`` tag).

        By default this titlises the column's :attr:`verbose_name`. If
        ``verbose_name`` is an instance of ``SafeData``, it's used unmodified.

        :returns: ``unicode`` or ``None``

        .. note::

            This property typically isn't accessed directly when a table is
            rendered. Instead, :attr:`.BoundColumn.header` is accessed which
            in turn accesses this property. This allows the header to fallback
            to the column name (it's only available on a :class:`.BoundColumn`
            object hence accessing that first) when this property doesn't
            return something useful.
        """
        if self.verbose_name:
            if isinstance(self.verbose_name, SafeData):
                # If the author has used mark_safe, we're going to assume the
                # author wants the value used verbatim.
                return self.verbose_name
            return title(self.verbose_name)

    def render(self, value):
        """
        Returns the content for a specific cell.

        This method can be overridden by :meth:`render_FOO` methods on the
        table or by subclassing :class:`Column`.

        :returns: `unicode`

        If the value for this cell is in `self.empty_values`, this method is
        skipped and an appropriate default value is rendered instead.
        Subclasses should set `empty_values` to `()` if they want to handle
        all values in `render`.
        """
        return value

    @property
    def sortable(self):
        """
        *deprecated* -- use `orderable` instead.
        """
        warnings.warn('`sortable` is deprecated, use `orderable` instead.',
                      DeprecationWarning)
        return self.orderable

    @classmethod
    def from_field(cls, field):
        """
        Return a specialised column for the model field or ``None``.

        :param field: the field that needs a suitable column
        :type  field: model field instance
        :returns: Column object or ``None``

        If the column isn't specialised for the given model field, it should
        return ``None``. This gives other columns the opportunity to do better.

        If the column is specialised, it should return an instance of itself
        that's configured appropriately for the field.
        """
        # Since this method is inherited by every subclass, only prove
        if cls is Column:
            return cls(verbose_name=field.verbose_name)


@library.register
class BooleanColumn(Column):
    """
    A column suitable for rendering boolean data.

    :param  null: is ``None`` different from ``False``?
    :type   null: bool
    :param yesno: text to display for True/False values, comma separated
    :type  yesno: iterable or string

    Rendered values are wrapped in a ``<span>`` to allow customisation by
    themes. By default the span is given the class ``true``, ``false``.

    In addition to ``attrs`` keys supported by ``Column``, the following are
    available:

    - *span* -- adds attributes to the <span> tag
    """
    def __init__(self, null=False, yesno="✔,✘", **kwargs):
        self.yesno = (yesno.split(',') if isinstance(yesno, basestring)
                                       else tuple(yesno))
        if null:
            kwargs[b"empty_values"] = ()
        super(BooleanColumn, self).__init__(**kwargs)

    def render(self, value):
        value = bool(value)
        text = self.yesno[int(not value)]
        html = '<span %s>%s</span>'
        attrs = {"class": unicode(value).lower()}
        attrs.update(self.attrs.get("span", {}))
        return mark_safe(html % (AttributeDict(attrs).as_html(), escape(text)))

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.BooleanField):
            return cls(verbose_name=field.verbose_name, null=False)
        if isinstance(field, models.NullBooleanField):
            return cls(verbose_name=field.verbose_name, null=True)


@library.register
class CheckBoxColumn(Column):
    """
    A subclass of :class:`.Column` that renders as a checkbox form input.

    This column allows a user to *select* a set of rows. The selection
    information can then be used to apply some operation (e.g. "delete") onto
    the set of objects that correspond to the selected rows.

    The value that is extracted from the :term:`table data` for this column is
    used as the value for the checkbox, i.e. ``<input type="checkbox"
    value="..." />``

    This class implements some sensible defaults:

    - HTML input's ``name`` attribute is the :term:`column name` (can override
      via ``attrs`` argument).
    - ``orderable`` defaults to :const:`False`.

    .. note::

        You'd expect that you could select multiple checkboxes in the rendered
        table and then *do something* with that. This functionality isn't
        implemented. If you want something to actually happen, you'll need to
        implement that yourself.

    In addition to ``attrs`` keys supported by ``Column``, the following are
    available:

    - *input*     -- ``<input>`` elements in both ``<td>`` and ``<th>``.
    - *th__input* -- Replaces *input* attrs in header cells.
    - *td__input* -- Replaces *input* attrs in body cells.
    """
    def __init__(self, attrs=None, **extra):
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

        kwargs = {b'orderable': False, b'attrs': attrs}
        kwargs.update(extra)
        super(CheckBoxColumn, self).__init__(**kwargs)

    @property
    def header(self):
        default = {'type': 'checkbox'}
        general = self.attrs.get('input')
        specific = self.attrs.get('th__input')
        attrs = AttributeDict(default, **(specific or general or {}))
        return mark_safe('<input %s/>' % attrs.as_html())

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


@library.register
class BaseLinkColumn(Column):
    """
    The base for other columns that render links.

    Adds support for an ``a`` key in ``attrs`` which is added to the rendered
    ``<a href="...">`` tag.
    """
    def __init__(self, attrs=None, *args, **kwargs):
        valid = set(("a", "th", "td", "cell"))
        if attrs and not set(attrs) & set(valid):
            # if none of the keys in attrs are actually valid, assume it's some
            # old code that should be be interpreted as {"a": ...}
            warnings.warn('attrs keys must be one of %s, interpreting as {"a": %s}'
                          % (', '.join(valid), attrs), DeprecationWarning)
            attrs = {"a": attrs}
        kwargs[b'attrs'] = attrs
        super(BaseLinkColumn, self).__init__(*args, **kwargs)

    def render_link(self, uri, text, attrs=None):
        """
        Render a hyperlink.

        :param   uri: URI for the hyperlink
        :param  text: value wrapped in ``<a></a>``
        :param attrs: ``<a>`` tag attributes
        """
        attrs = AttributeDict(attrs if attrs is not None else
                              self.attrs.get('a', {}))
        html = '<a href="{uri}"{attrs}>{text}</a>'.format(
            uri=escape(uri),
            attrs=" %s" % attrs.as_html() if attrs else "",
            text=escape(text)
        )
        return mark_safe(html)


@library.register
class LinkColumn(BaseLinkColumn):
    """
    Renders a normal value as an internal hyperlink to another page.

    It's common to have the primary value in a row hyperlinked to the page
    dedicated to that record.

    The first arguments are identical to that of
    :func:`django.core.urlresolvers.reverse` and allows an internal URL to be
    described. The last argument ``attrs`` allows custom HTML attributes to
    be added to the rendered ``<a href="...">`` tag.

    :param    viewname: See :func:`django.core.urlresolvers.reverse`.
    :param     urlconf: See :func:`django.core.urlresolvers.reverse`.
    :param        args: See :func:`django.core.urlresolvers.reverse`. **
    :param      kwargs: See :func:`django.core.urlresolvers.reverse`. **
    :param current_app: See :func:`django.core.urlresolvers.reverse`.
    :param       attrs: a :class:`dict` of HTML attributes that are added to
                        the rendered ``<input type="checkbox" .../>`` tag

    ** In order to create a link to a URL that relies on information in the
    current row, :class:`.Accessor` objects can be used in the ``args`` or
    ``kwargs`` arguments. The accessor will be resolved using the row's record
    before ``reverse()`` is called.

    Example:

    .. code-block:: python

        # models.py
        class Person(models.Model):
            name = models.CharField(max_length=200)

        # urls.py
        urlpatterns = patterns('',
            url('people/(\d+)/', views.people_detail, name='people_detail')
        )

        # tables.py
        from django_tables2.utils import A  # alias for Accessor

        class PeopleTable(tables.Table):
            name = tables.LinkColumn('people_detail', args=[A('pk')])

    In addition to ``attrs`` keys supported by ``Column``, the following are
    available:

    - *a* -- ``<a>`` elements in ``<td>``.
    """
    def __init__(self, viewname, urlconf=None, args=None, kwargs=None,
                 current_app=None, attrs=None, **extra):
        super(LinkColumn, self).__init__(attrs, **extra)
        self.viewname = viewname
        self.urlconf = urlconf
        self.args = args
        self.kwargs = kwargs
        self.current_app = current_app

    def render(self, value, record, bound_column):  # pylint: disable=W0221
        # The following params + if statements create the arguments required to
        # pass to Django's reverse() function.
        params = {}
        if self.viewname:
            params[b'viewname'] = (self.viewname.resolve(record)
                                 if isinstance(self.viewname, A)
                                 else self.viewname)
        if self.urlconf:
            params[b'urlconf'] = (self.urlconf.resolve(record)
                                 if isinstance(self.urlconf, A)
                                 else self.urlconf)
        if self.args:
            params[b'args'] = [a.resolve(record) if isinstance(a, A) else a
                              for a in self.args]
        if self.kwargs:
            params[b'kwargs'] = {}
            for key, val in self.kwargs.items():
                # If we're dealing with an Accessor (A), resolve it, otherwise
                # use the value verbatim.
                params[b'kwargs'][str(key)] = (val.resolve(record)
                                               if isinstance(val, A) else val)
        if self.current_app:
            params[b'current_app'] = (self.current_app.resolve(record)
                                     if isinstance(self.current_app, A)
                                     else self.current_app)
        return self.render_link(reverse(**params), value)


@library.register
class URLColumn(BaseLinkColumn):
    """
    A subclass of :class:`.BaseLinkColumn` that renders the cell value as a hyperlink.

    It's common to have a URL value in a row hyperlinked to other page.

    :param  attrs: a :class:`dict` of HTML attributes that are added to
                   the rendered ``<a href="...">...</a>`` tag

    Example:

    .. code-block:: python

        # models.py
        class Person(models.Model):
            name = models.CharField(max_length=200)
            web =  models.URLField()

        # tables.py
        class PeopleTable(tables.Table):
            name = tables.Column()
            web = tables.URLColumn()

    """
    def render(self, value):
        return self.render_link(value, value)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.URLField):
            return cls(verbose_name=field.verbose_name)


@library.register
class EmailColumn(BaseLinkColumn):
    """
    A subclass of :class:`.BaseLinkColumn` that renders the cell value as a hyperlink.

    It's common to have a email value in a row hyperlinked to other page.

    :param  attrs: a :class:`dict` of HTML attributes that are added to
                   the rendered ``<a href="...">...</a>`` tag

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
    def render(self, value):
        return self.render_link("mailto:%s" % value, value)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.EmailField):
            return cls(verbose_name=field.verbose_name)


@library.register
class TemplateColumn(Column):
    """
    A subclass of :class:`.Column` that renders some template code to use as
    the cell value.

    :type  template_code: `unicode`
    :param template_code: the template code to render
    :type  template_name: `unicode`
    :param template_name: the name of the template to render

    A :class:`django.templates.Template` object is created from the
    *template_code* or *template_name* and rendered with a context containing:

    - `record` -- data record for the current row
    - `value` -- value from `record` that corresponds to the current column
    - `default` -- appropriate default value to use as fallback

    Example:

    .. code-block:: python

        class ExampleTable(tables.Table):
            foo = tables.TemplateColumn('{{ record.bar }}')
            # contents of `myapp/bar_column.html` is `{{ value }}`
            bar = tables.TemplateColumn(template_name='myapp/name2_column.html')

    Both columns will have the same output.

    .. important::

        In order to use template tags or filters that require a
        ``RequestContext``, the table **must** be rendered via
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
                        'record': record, 'value': value})
        try:
            if self.template_code:
                return Template(self.template_code).render(context)
            else:
                return render_to_string(self.template_name, context)
        finally:
            context.pop()


@library.register
class DateColumn(TemplateColumn):
    """
    A column that renders dates in the local timezone.

    :param format: format string in same format as Django's ``date`` template
                   filter (optional)
    :type  format: ``unicode``
    :param  short: if ``format`` is not specified, use Django's
                   ``SHORT_DATE_FORMAT`` setting, otherwise use ``DATE_FORMAT``
    :type   short: ``bool``
    """
    def __init__(self, format=None, short=True, *args, **kwargs):
        if format is None:
            format = 'SHORT_DATE_FORMAT' if short else 'DATE_FORMAT'
        template = '{{ value|date:"%s"|default:default }}' % format
        super(DateColumn, self).__init__(template_code=template, *args, **kwargs)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.DateField):
            return cls(verbose_name=field.verbose_name)


@library.register
class DateTimeColumn(TemplateColumn):
    """
    A column that renders datetimes in the local timezone.

    :param format: format string for datetime (optional)
    :type  format: ``unicode``
    :param  short: if ``format`` is not specifid, use Django's
                   ``SHORT_DATETIME_FORMAT``, else ``DATETIME_FORMAT``
    :type   short: ``bool``
    """
    def __init__(self, format=None, short=True, *args, **kwargs):
        if format is None:
            format = 'SHORT_DATETIME_FORMAT' if short else 'DATETIME_FORMAT'
        template = '{{ value|date:"%s"|default:default }}' % format
        super(DateTimeColumn, self).__init__(template_code=template, *args, **kwargs)

    @classmethod
    def from_field(cls, field):
        if isinstance(field, models.DateTimeField):
            return cls(verbose_name=field.verbose_name)


class BoundColumn(object):
    """
    A *run-time* version of :class:`.Column`. The difference between
    ``BoundColumn`` and ``Column``, is that ``BoundColumn`` objects include the
    relationship between a ``Column`` and a :class:`.Table`. In practice, this
    means that a ``BoundColumn`` knows the *"variable name"* given to the
    ``Column`` when it was declared on the ``Table``.

    For convenience, all :class:`.Column` properties are available from this
    class.

    :type   table: :class:`.Table` object
    :param  table: the table in which this column exists
    :type  column: :class:`.Column` object
    :param column: the type of column
    :type    name: ``basestring`` object
    :param   name: the variable name of the column used to when defining the
                   :class:`.Table`. In this example the name is ``age``:

                       .. code-block:: python

                           class SimpleTable(tables.Table):
                               age = tables.Column()

    """
    def __init__(self, table, column, name):
        self.table = table
        self.column = column
        self.name = name

    def __unicode__(self):
        return unicode(self.header)

    @property
    def accessor(self):
        """
        Returns the string used to access data for this column out of the data
        source.
        """
        return self.column.accessor or A(self.name)

    @property
    def attrs(self):
        """
        Proxy to ``Column.attrs`` but injects some values of our own.

        A ``th`` and ``td`` are guaranteed to be defined (irrespective of
        what's actually defined in the column attrs. This makes writing
        templates easier.
        """
        # Work on a copy of the attrs object since we're tweaking stuff
        attrs = dict(self.column.attrs)

        # Find the relevant th attributes (fall back to cell if th isn't
        # explicitly specified).
        attrs["td"] = td = AttributeDict(attrs.get('td', attrs.get('cell', {})))
        attrs["th"] = th = AttributeDict(attrs.get("th", attrs.get("cell", {})))
        # make set of existing classes.
        th_class = set((c for c in th.get("class", "").split(" ") if c))  # pylint: disable=C0103
        td_class = set((c for c in td.get("class", "").split(" ") if c))  # pylint: disable=C0103
        # add classes for ordering
        if self.orderable:
            th_class.add("orderable")
            th_class.add("sortable")  # backwards compatible
        if self.is_ordered:
            th_class.add("desc" if self.order_by_alias.is_descending else "asc")
        # Always add the column name as a class
        th_class.add(self.name)
        td_class.add(self.name)
        if th_class:
            th['class'] = " ".join(sorted(th_class))
        if td_class:
            td['class'] = " ".join(sorted(td_class))
        return attrs

    @property
    def default(self):
        """
        Returns the default value for this column.
        """
        value = self.column.default
        if value is None:
            value = self.table.default
        return value

    @property
    def header(self):
        """
        The value that should be used in the header cell for this column.
        """
        # favour Column.header
        column_header = self.column.header
        if column_header:
            return column_header
        # fall back to automatic best guess
        verbose_name = self.verbose_name  # avoid calculating multiple times
        if isinstance(verbose_name, SafeData):
            # If the verbose_name has come from a model field, it's possible
            # that the author used mark_safe to include HTML in the value. If
            # this is the case, we leave it verbatim.
            return verbose_name
        return title(verbose_name)

    @property
    def order_by(self):
        """
        Returns an :class:`OrderByTuple` of appropriately prefixed data source
        keys used to sort this column.

        See :meth:`.order_by_alias` for details.
        """
        if self.column.order_by is not None:
            order_by = self.column.order_by
        else:
            # default to using column accessor as data source sort key
            order_by = OrderByTuple((self.accessor, ))
        return order_by.opposite if self.order_by_alias.is_descending else order_by

    @property
    def order_by_alias(self):
        """
        Returns an :class:`OrderBy` describing the current state of ordering
        for this column.

        The following attempts to explain the difference between ``order_by``
        and ``order_by_alias``.

        ``order_by_alias`` returns and ``OrderBy`` instance that's based on
        the *name* of the column, rather than the keys used to order the table
        data. Understanding the difference is essential.

        Having an alias *and* a keys version is necessary because an N-tuple
        (of data source keys) can be used by the column to order the data, and
        it's ambiguous when mapping from N-tuple to column (since multiple
        columns could use the same N-tuple).

        The solution is to use order by *aliases* (which are really just
        prefixed column names) that describe the ordering *state* of the
        column, rather than the specific keys in the data source should be
        ordered.

        e.g.::

            >>> class SimpleTable(tables.Table):
            ...     name = tables.Column(order_by=("firstname", "last_name"))
            ...
            >>> table = SimpleTable([], order_by=("-name", ))
            >>> table.columns["name"].order_by_alias
            "-name"
            >>> table.columns["name"].order_by
            ("-first_name", "-last_name")

        The ``OrderBy`` returned has been patched to include an extra attribute
        ``next``, which returns a version of the alias that would be
        transitioned to if the user toggles sorting on this column, e.g.::

            not sorted -> ascending
            ascending  -> descending
            descending -> ascending

        This is useful otherwise in templates you'd need something like:

            {% if column.is_ordered %}
            {% querystring table.prefixed_order_by_field=column.order_by_alias.opposite %}
            {% else %}
            {% querystring table.prefixed_order_by_field=column.order_by_alias %}
            {% endif %}

        """
        order_by = OrderBy((self.table.order_by or {}).get(self.name, self.name))
        order_by.next = order_by.opposite if self.is_ordered else order_by
        return order_by

    @property
    def is_ordered(self):
        return self.name in (self.table.order_by or ())

    @property
    def sortable(self):
        """
        *deprecated* -- use `orderable` instead.
        """
        warnings.warn('`%s.sortable` is deprecated, use `orderable`'
                      % type(self).__name__, DeprecationWarning)
        return self.orderable

    @property
    def orderable(self):
        """
        Return a ``bool`` depending on whether this column supports ordering.
        """
        if self.column.orderable is not None:
            return self.column.orderable
        return self.table.orderable

    @property
    def verbose_name(self):
        """
        Return the verbose name for this column, or fallback to prettified
        column name.

        If the table is using queryset data, then use the corresponding
        model field's ``verbose_name``. If it's traversing a relationship,
        then get the last field in the accessor (i.e. stop when the
        relationship turns from ORM relationships to object attributes [e.g.
        person.upper should stop at person]).

        If the model field's ``verbose_name`` is a ``SafeData``, it's used
        unmodified.
        """
        # Favor an explicit defined verbose_name
        if self.column.verbose_name:
            return self.column.verbose_name

        # This is our reasonable fallback, should the next section not result
        # in anything useful.
        name = self.name.replace('_', ' ')

        # Try to use a tmodel field's verbose_name
        if hasattr(self.table.data, 'queryset'):
            model = self.table.data.queryset.model
            parts = self.accessor.split('.')
            field = None
            for part in parts:
                try:
                    field = model._meta.get_field(part)
                except FieldDoesNotExist:
                    break
                if hasattr(field, 'rel') and hasattr(field.rel, 'to'):
                    model = field.rel.to
                    continue
                break
            if field:
                name = field.verbose_name
        return name

    @property
    def visible(self):
        """
        Returns a :class:`bool` depending on whether this column is visible.
        """
        return self.column.visible


class BoundColumns(object):
    """
    Container for spawning :class:`.BoundColumn` objects.

    This is bound to a table and provides its :attr:`.Table.columns` property.
    It provides access to those columns in different ways (iterator,
    item-based, filtered and unfiltered etc), stuff that would not be possible
    with a simple iterator in the table class.

    A ``BoundColumns`` object is a container for holding
    ``BoundColumn`` objects. It provides methods that make accessing
    columns easier than if they were stored in a ``list`` or
    ``dict``. ``Columns`` has a similar API to a ``dict`` (it
    actually uses a ``SortedDict`` interally).

    At the moment you'll only come across this class when you access a
    :attr:`.Table.columns` property.

    :type  table: :class:`.Table` object
    :param table: the table containing the columns
    """
    def __init__(self, table):
        self.table = table
        self.columns = SortedDict()
        for name, column in self.table.base_columns.iteritems():
            self.columns[name] = BoundColumn(self.table, column, name)

        # Prepare each column's ``render`` function and its expected argument
        # so they can be easily called when each row is iterated.
        for name, bound_column in self.iteritems():
            bound_column.render = getattr(self.table, 'render_' + bound_column.name,
                                          bound_column.column.render)
            bound_column._render_args = getargspec(bound_column.render).args[1:]

    def iternames(self):
        return (name for name, column in self.iteritems())

    def names(self):
        return list(self.iternames())

    def iterall(self):
        """
        Return an iterator that exposes all :class:`.BoundColumn` objects,
        regardless of visiblity or sortability.
        """
        return (column for name, column in self.iteritems())

    def all(self):
        return list(self.iterall())

    def iteritems(self):
        """
        Return an iterator of ``(name, column)`` pairs (where ``column`` is a
        :class:`.BoundColumn` object).

        This method is the mechanism for retrieving columns that takes into
        consideration all of the ordering and filtering modifiers that a table
        supports (e.g. ``exclude`` and ``sequence``).
        """
        for name in self.table.sequence:
            if name not in self.table.exclude:
                yield (name, self.columns[name])

    def items(self):
        return list(self.iteritems())

    def iterorderable(self):
        """
        Same as :meth:`.BoundColumns.all` but only returns orderable columns.

        This is useful in templates, where iterating over the full
        set and checking ``{% if column.sortable %}`` can be problematic in
        conjunction with e.g. ``{{ forloop.last }}`` (the last column might not
        be the actual last that is rendered).
        """
        return ifilter(lambda x: x.orderable, self.iterall())

    def itersortable(self):
        warnings.warn('`itersortable` is deprecated, use `iterorderable` instead.',
                      DeprecationWarning)
        return self.iterorderable()

    def orderable(self):
        return list(self.iterorderable())

    def sortable(self):
        warnings.warn("`sortable` is deprecated, use `orderable` instead.",
                      DeprecationWarning)
        return self.orderable

    def itervisible(self):
        """
        Same as :meth:`.iterorderable` but only returns visible
        :class:`.BoundColumn` objects.

        This is geared towards table rendering.
        """
        return ifilter(lambda x: x.visible, self.iterall())

    def visible(self):
        return list(self.itervisible())

    def __iter__(self):
        """
        Convenience API, alias of :meth:`.itervisible`.
        """
        return self.itervisible()

    def __contains__(self, item):
        """
        Check if a column is contained within a :class:`.Columns` object.

        *item* can either be a :class:`.BoundColumn` object, or the name of a
        column.
        """
        if isinstance(item, basestring):
            return item in self.iternames()
        else:
            # let's assume we were given a column
            return item in self.iterall()

    def __len__(self):
        """
        Return how many :class:`BoundColumn` objects are contained (and
        visible).
        """
        return len(self.visible())

    def __getitem__(self, index):
        """
        Retrieve a specific :class:`BoundColumn` object.

        *index* can either be 0-indexed or the name of a column

        .. code-block:: python

            columns['speed']  # returns a bound column with name 'speed'
            columns[0]        # returns the first column
        """
        if isinstance(index, int):
            try:
                return next(islice(self.iterall(), index, index + 1))
            except StopIteration:
                raise IndexError
        elif isinstance(index, basestring):
            for column in self.iterall():
                if column.name == index:
                    return column
            raise KeyError("Column with name '%s' does not exist; "
                           "choices are: %s" % (index, self.names()))
        else:
            raise TypeError('row indices must be integers or str, not %s'
                            % type(index).__name__)


# A dict of ``{model_field: column, ...}``
model_field_columns = defaultdict(lambda: Column, **{
    models.DateTimeField: DateTimeColumn,
    models.DateField: DateColumn,
    })
