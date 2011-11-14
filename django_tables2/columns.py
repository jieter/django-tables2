# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode, StrAndUnicode
from django.utils.datastructures import SortedDict
from django.utils.text import capfirst
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.template import RequestContext, Context, Template
from django.db.models.fields import FieldDoesNotExist
from .utils import A, AttributeDict, OrderBy, Sequence
from itertools import ifilter, islice


class Column(object):
    """
    Represents a single column of a table.

    :class:`Column` objects control the way a column (including the cells that
    fall within it) are rendered.

    :param verbose_name: A human readable version of the column name.
        Typically this is used in the header cells in the HTML output. (But if
        you're writing your own template, use ``.header`` rather than
        ``.verbose_name``)

    :type accessor: :class:`basestring` or :class:`~.utils.Accessor`
    :param accessor: An accessor that describes how to extract values for this
        column from the :term:`table data`.

    :param default: The default value for the column. This can be a value or a
        callable object [1]_. If an object in the data provides :const:`None`
        for a column, the default will be used instead.

        The default value may affect ordering, depending on the type of
        data the table is using. The only case where ordering is not
        affected ing when a :class:`QuerySet` is used as the table data
        (since sorting is performed by the database).

        .. [1] The provided callable object must not expect to receive any
           arguments.

    :type visible: :class:`bool`
    :param visible: If :const:`False`, this column will not be in HTML from
        output generators (e.g. :meth:`as_html` or ``{% render_table %}``).

        When a field is not visible, it is removed from the table's
        :attr:`~Column.columns` iterable.

    :type sortable: :class:`bool`
    :param sortable: If :const:`False`, this column will not be allowed to
        influence row ordering/sorting.
    """
    #: Tracks each time a Column instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, verbose_name=None, accessor=None, default=None,
                 visible=True, sortable=None):
        if not (accessor is None or isinstance(accessor, basestring) or
                callable(accessor)):
            raise TypeError(u'accessor must be a string or callable, not %s' %
                            accessor.__class__.__name__)
        if callable(accessor) and default is not None:
            raise TypeError('accessor must be string when default is used, not'
                            ' callable')
        self.accessor = A(accessor) if accessor else None
        self._default = default
        self.sortable = sortable
        self.verbose_name = verbose_name
        self.visible = visible

        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

    @property
    def default(self):
        """
        The default value for cells in this column.

        The default value passed into ``Column.default`` property may be a
        callable, this function handles access.
        """
        return self._default() if callable(self._default) else self._default

    @property
    def header(self):
        """
        The value used for the column heading (e.g. inside the ``<th>`` tag).

        By default this equivalent to the column's :attr:`verbose_name`.

        .. note::

            This property typically isn't accessed directly when a table is
            rendered. Instead, :attr:`.BoundColumn.header` is accessed which
            in turn accesses this property. This allows the header to fallback
            to the column name (it's only available on a :class:`.BoundColumn`
            object hence accessing that first) when this property doesn't
            return something useful.
        """
        return self.verbose_name

    def render(self, value):
        """
        Returns the content for a specific cell.

        This method can be overridden by :meth:`render_FOO` methods on the
        table or by subclassing :class:`Column`.
        """
        return value


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

    - The ``name`` attribute of the input is the name of the :term:`column
      name` (can be overriden via ``attrs`` argument).
    - The ``sortable`` parameter defaults to :const:`False`.
    - The ``type`` attribute of the input is ``checkbox`` (can be overriden via
      ``attrs`` argument).
    - The header checkbox is left bare, i.e. ``<input type="checkbox"/>`` (use
      the ``header_attrs`` argument to customise).

    .. note:: The "apply some operation onto the selection" functionality is
        not implemented in this column, and requires manually implemention.

    :param attrs:
        a :class:`dict` of HTML attributes that are added to the rendered
        ``<input type="checkbox" .../>`` tag
    :param header_attrs:
        same as *attrs*, but applied **only** to the header checkbox
    """
    def __init__(self, attrs=None, header_attrs=None, **extra):
        params = {'sortable': False}
        params.update(extra)
        super(CheckBoxColumn, self).__init__(**params)
        self.attrs = attrs or {}
        self.header_attrs = header_attrs or {}

    @property
    def header(self):
        attrs = AttributeDict({
            'type': 'checkbox',
        })
        attrs.update(self.header_attrs)
        return mark_safe(u'<input %s/>' % attrs.as_html())

    def render(self, value, bound_column):
        attrs = AttributeDict({
            'type': 'checkbox',
            'name': bound_column.name,
            'value': value
        })
        attrs.update(self.attrs)
        return mark_safe(u'<input %s/>' % attrs.as_html())


class LinkColumn(Column):
    """
    A subclass of :class:`.Column` that renders the cell value as a hyperlink.

    It's common to have the primary value in a row hyperlinked to page
    dedicated to that record.

    The first arguments are identical to that of
    :func:`django.core.urlresolvers.reverse` and allow a URL to be
    described. The last argument ``attrs`` allows custom HTML attributes to
    be added to the ``<a>`` tag.

    :param viewname: See :func:`django.core.urlresolvers.reverse`.
    :param urlconf: See :func:`django.core.urlresolvers.reverse`.
    :param args: See :func:`django.core.urlresolvers.reverse`. **
    :param kwargs: See :func:`django.core.urlresolvers.reverse`. **
    :param current_app: See :func:`django.core.urlresolvers.reverse`.

    :param attrs:
        a :class:`dict` of HTML attributes that are added to the rendered
        ``<input type="checkbox" .../>`` tag

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
    """
    def __init__(self, viewname, urlconf=None, args=None, kwargs=None,
                 current_app=None, attrs=None, **extra):
        super(LinkColumn, self).__init__(**extra)
        self.viewname = viewname
        self.urlconf = urlconf
        self.args = args
        self.kwargs = kwargs
        self.current_app = current_app
        self.attrs = attrs or {}

    def render(self, value, record, bound_column):
        # Remember that value is actually what would have normally been put
        # into the cell. i.e. it *already* takes into consideration the
        # column's *default* property, thus we must check the actual data value
        # and use that to decide whether to render a link or just the default
        try:
            raw = bound_column.accessor.resolve(record)
        except (TypeError, AttributeError, KeyError, ValueError) as e:
            raw = None
        if raw is None:
            return self.default
        # The following params + if statements create the arguments required to
        # pass to Django's reverse() function.
        params = {}
        if self.viewname:
            params['viewname'] = (self.viewname.resolve(record)
                                 if isinstance(self.viewname, A)
                                 else self.viewname)
        if self.urlconf:
            params['urlconf'] = (self.urlconf.resolve(record)
                                 if isinstance(self.urlconf, A)
                                 else self.urlconf)
        if self.args:
            params['args'] = [a.resolve(record) if isinstance(a, A) else a
                              for a in self.args]
        if self.kwargs:
            params['kwargs'] = {}
            for k, v in self.kwargs.items():
                # If we're dealing with an Accessor (A), resolve it, otherwise
                # use the value verbatim.
                params['kwargs'][k] = (v.resolve(record) if isinstance(v, A)
                                       else v)
        if self.current_app:
            params['current_app'] = (self.current_app.resolve(record)
                                     if isinstance(self.current_app, A)
                                     else self.current_app)
        print 'params =', params
        html = u'<a href="{url}" {attrs}>{value}</a>'.format(
            url=reverse(**params),
            attrs=AttributeDict(self.attrs).as_html(),
            value=escape(value)
        )
        return mark_safe(html)


class TemplateColumn(Column):
    """
    A subclass of :class:`.Column` that renders some template code to use as
    the cell value.

    :type template_code: :class:`basestring` object
    :param template_code: the template code to render

    A :class:`django.templates.Template` object is created from the
    *template_code* and rendered with a context containing only a ``record``
    variable. This variable is the record for the table row being rendered.

    Example:

    .. code-block:: python

        class SimpleTable(tables.Table):
            name1 = tables.TemplateColumn('{{ record.name }}')
            name2 = tables.Column()

    Both columns will have the same output.

    .. important::

        In order to use template tags or filters that require a
        ``RequestContext``, the table **must** be rendered via
        :ref:`{% render_table %} <template-tags.render_table>`.
    """
    def __init__(self, template_code=None, **extra):
        super(TemplateColumn, self).__init__(**extra)
        self.template_code = template_code

    def render(self, record, table, **kwargs):
        t = Template(self.template_code)
        if hasattr(table, 'request'):
            context = RequestContext(table.request, {'record': record})
        else:
            context = Context({'record': record})
        return t.render(context)


class BoundColumn(object):
    """
    A *run-time* version of :class:`.Column`. The difference between
    ``BoundColumn`` and ``Column``, is that ``BoundColumn`` objects include the
    relationship between a ``Column`` and a :class:`.Table`. In practice, this
    means that a ``BoundColumn`` knows the *"variable name"* given to the
    ``Column`` when it was declared on the ``Table``.

    For convenience, all :class:`.Column` properties are available from this
    class.

    :type table: :class:`.Table` object
    :param table: the table in which this column exists

    :type column: :class:`.Column` object
    :param column: the type of column

    :type name: ``basestring`` object
    :param name: the variable name of the column used to when defining the
        :class:`.Table`. Example:

        .. code-block:: python

            class SimpleTable(tables.Table):
                age = tables.Column()

        ``age`` is the name.
    """
    def __init__(self, table, column, name):
        self._table = table
        self._column = column
        self._name = name

    def __unicode__(self):
        return unicode(self.verbose_name)

    @property
    def accessor(self):
        """
        Returns the string used to access data for this column out of the data
        source.
        """
        return self.column.accessor or A(self.name)

    @property
    def column(self):
        """
        Returns the :class:`.Column` object for this column.
        """
        return self._column

    @property
    def default(self):
        """
        Returns the default value for this column.
        """
        return self.column.default

    @property
    def header(self):
        """
        The value that should be used in the header cell for this column.
        """
        return self.column.header or self.verbose_name

    @property
    def name(self):
        """
        Returns the string used to identify this column.
        """
        return self._name

    @property
    def order_by(self):
        """
        If this column is sorted, return the associated :class:`.OrderBy`
        instance, otherwise ``None``.
        """
        try:
            return self.table.order_by[self.name]
        except IndexError:
            return None

    @property
    def sortable(self):
        """
        Return a ``bool`` depending on whether this column is sortable.
        """
        if self.column.sortable is not None:
            return self.column.sortable
        return self.table.sortable

    @property
    def table(self):
        """
        Return the :class:`Table` object that this column is part of.
        """
        return self._table

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
        return capfirst(name)

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

    :type table: :class:`.Table` object
    :param table: the table containing the columns
    """
    def __init__(self, table):
        self.table = table

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
        # First we build a sorted dict of all the columns that we need.
        columns = SortedDict()
        for name, column in self.table.base_columns.iteritems():
            columns[name] = BoundColumn(self.table, column, name)

        # A list of column names in the correct sequence that they should be
        # rendered in the table.
        sequence = (self.table.sequence or Sequence(('...', )))
        sequence.expand(self.table.base_columns.keys())

        for name in sequence:
            if name not in self.table.exclude:
                yield (name, columns[name])

    def items(self):
        return list(self.iteritems())

    def itersortable(self):
        """
        Same as :meth:`.BoundColumns.all` but only returns sortable
        :class:`.BoundColumn` objects.

        This is useful in templates, where iterating over the full
        set and checking ``{% if column.sortable %}`` can be problematic in
        conjunction with e.g. ``{{ forloop.last }}`` (the last column might not
        be the actual last that is rendered).
        """
        return ifilter(lambda x: x.sortable, self.iterall())

    def sortable(self):
        return list(self.itersortable())

    def itervisible(self):
        """
        Same as :meth:`.sortable` but only returns visible
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
                return next(islice(self.iterall(), index, index+1))
            except StopIteration:
                raise IndexError
        elif isinstance(index, basestring):
            for column in self.iterall():
                if column.name == index:
                    return column
            raise KeyError("Column with name '%s' does not exist." % index)
        else:
            raise TypeError(u'row indices must be integers or str, not %s'
                            % index.__class__.__name__)
