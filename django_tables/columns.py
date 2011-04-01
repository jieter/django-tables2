# -*- coding: utf-8 -*-
from django.core.urlresolvers import reverse
from django.utils.encoding import force_unicode, StrAndUnicode
from django.utils.datastructures import SortedDict
from django.utils.text import capfirst
from django.utils.safestring import mark_safe
from django.template import Context, Template
from .utils import OrderBy, A, AttributeDict


class Column(object):
    """Represents a single column of a table.

    :class:`Column` objects control the way a column (including the cells that
    fall within it) are rendered.

    """
    #: Tracks each time a Column instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, verbose_name=None, accessor=None, default=None,
                 visible=True, sortable=None):
        """Initialise a :class:`Column` object.

        :param verbose_name:
            A pretty human readable version of the column name. Typically this
            is used in the header cells in the HTML output.

        :param accessor:
            A string or callable that specifies the attribute to access when
            retrieving the value for a cell in this column from the data-set.
            Multiple lookups can be achieved by providing a dot separated list
            of lookups, e.g. ``"user.first_name"``. The functionality is
            identical to that of Django's template variable syntax, e.g. ``{{
            user.first_name }}``

            A callable should be used if the dot separated syntax is not
            capable of describing the lookup properly. The callable will be
            passed a single item from the data (if the table is using
            :class:`QuerySet` data, this would be a :class:`Model` instance),
            and is expected to return the correct value for the column.

            Consider the following:

            .. code-block:: python

                >>> import django_tables as tables
                >>> data = [
                ...     {'dot.separated.key': 1},
                ...     {'dot.separated.key': 2},
                ... ]
                ...
                >>> class SlightlyComplexTable(tables.Table):
                >>>     dot_seperated_key = tables.Column(accessor=lambda x: x['dot.separated.key'])
                ...
                >>> table = SlightlyComplexTable(data)
                >>> for row in table.rows:
                >>>     print row['dot_seperated_key']
                ...
                1
                2

            This would **not** have worked:

            .. code-block:: python

                dot_seperated_key = tables.Column(accessor='dot.separated.key')

        :param default:
            The default value for the column. This can be a value or a callable
            object [1]_. If an object in the data provides :const:`None` for a
            column, the default will be used instead.

            The default value may affect ordering, depending on the type of
            data the table is using. The only case where ordering is not
            affected ing when a :class:`QuerySet` is used as the table data
            (since sorting is performed by the database).

            .. [1] The provided callable object must not expect to receive any
               arguments.

        :param visible:
            If :const:`False`, this column will not be in HTML from output
            generators (e.g. :meth:`as_html` or ``{% render_table %}``).

            When a field is not visible, it is removed from the table's
            :attr:`~Column.columns` iterable.

        :param sortable:
            If :const:`False`, this column will not be allowed to be used in
            ordering the table.

        """
        if not (accessor is None or isinstance(accessor, basestring) or
                callable(accessor)):
            raise TypeError('accessor must be a string or callable, not %s' %
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
        """The default value for cells in this column.

        The default value passed into ``Column.default`` property may be a
        callable, this function handles access.

        """
        return self._default() if callable(self._default) else self._default

    def render(self, value, **kwargs):
        """Returns a cell's content.
        This method can be overridden by ``render_FOO`` methods on the table or
        by subclassing :class:`Column`.

        """
        return value


class CheckBoxColumn(Column):
    """A subclass of Column that renders its column data as a checkbox"""
    def __init__(self, attrs=None, **extra):
        """
        :param attrs: a dict of HTML element attributes to be added to the
            ``<input>``

        """
        params = {'sortable': False}
        params.update(extra)
        super(CheckBoxColumn, self).__init__(**params)
        self.attrs = attrs or {}
        self.verbose_name = mark_safe('<input type="checkbox"/>')

    def render(self, value, bound_column, **kwargs):
        attrs = AttributeDict({
            'type': 'checkbox',
            'name': bound_column.name,
            'value': value
        })
        attrs.update(self.attrs)
        return mark_safe('<input %s/>' % AttributeDict(attrs).as_html())



class LinkColumn(Column):
    def __init__(self, viewname, urlconf=None, args=None, kwargs=None,
                 current_app=None, attrs=None, **extra):
        """
        The first arguments are identical to that of
        :func:`django.core.urlresolvers.reverse` and allow a URL to be
        described. The last argument ``attrs`` allows custom HTML attributes to
        be added to the ``<a>`` tag.
        """
        super(LinkColumn, self).__init__(**extra)
        self.viewname = viewname
        self.urlconf = urlconf
        self.args = args
        self.kwargs = kwargs
        self.current_app = current_app
        self.attrs = attrs or {}

    def render(self, value, record, bound_column, **kwargs):
        params = {}  # args for reverse()
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
            params['kwargs'] = self.kwargs
            for key, value in self.kwargs:
                if isinstance(value, A):
                    params['kwargs'][key] = value.resolve(record)
        if self.current_app:
            params['current_app'] = self.current_app
            for key, value in self.current_app:
                if isinstance(value, A):
                    params['current_app'][key] = value.resolve(record)
        url = reverse(**params)
        html = '<a href="{url}" {attrs}>{value}</a>'.format(
            url=reverse(**params),
            attrs=AttributeDict(self.attrs).as_html(),
            value=value
        )
        return mark_safe(html)


class TemplateColumn(Column):
    def __init__(self, template_code=None, **extra):
        super(TemplateColumn, self).__init__(**extra)
        self.template_code = template_code

    def render(self, record, **kwargs):
        t = Template(self.template_code)
        return t.render(Context({'record': record}))


class BoundColumn(object):
    """A *runtime* version of :class:`Column`. The difference between
    :class:`BoundColumn` and :class:`Column`, is that :class:`BoundColumn`
    objects are of the relationship between a :class:`Column` and a
    :class:`Table`. This means that it knows the *name* given to the
    :class:`Column`.

    For convenience, all :class:`Column` properties are available from this
    class.

    """
    def __init__(self, table, column, name):
        """Initialise a :class:`BoundColumn` object where:

        * *table* - a :class:`Table` object in which this column exists
        * *column* - a :class:`Column` object
        * *name* – the variable name used when the column was added to the
                   :class:`Table` subclass

        """
        self._table = table
        self._column = column
        self._name = name

    def __unicode__(self):
        return self.verbose_name

    @property
    def table(self):
        """Returns the :class:`Table` object that this column is part of."""
        return self._table

    @property
    def column(self):
        """Returns the :class:`Column` object for this column."""
        return self._column

    @property
    def name(self):
        """Returns the string used to identify this column."""
        return self._name

    @property
    def accessor(self):
        """Returns the string used to access data for this column out of the
        data source.

        """
        return self.column.accessor or A(self.name)

    @property
    def default(self):
        """Returns the default value for this column."""
        return self.column.default

    @property
    def sortable(self):
        """Returns a ``bool`` depending on whether this column is sortable."""
        if self.column.sortable is not None:
            return self.column.sortable
        elif self.table._meta.sortable is not None:
            return self.table._meta.sortable
        else:
            return True  # the default value

    @property
    def verbose_name(self):
        """Returns the verbose name for this column."""
        return (self.column.verbose_name
                or capfirst(force_unicode(self.name.replace('_', ' '))))

    @property
    def visible(self):
        """Returns a ``bool`` depending on whether this column is visible."""
        return self.column.visible

    @property
    def order_by(self):
        """If this column is sorted, return the associated OrderBy instance.
        Otherwise return a None.

        """
        try:
            return self.table.order_by[self.name]
        except IndexError:
            return None


class Columns(object):
    """Container for spawning BoundColumns.

    This is bound to a table and provides its ``columns`` property. It
    provides access to those columns in different ways (iterator,
    item-based, filtered and unfiltered etc), stuff that would not be
    possible with a simple iterator in the table class.

    A :class:`Columns` object is a container for holding :class:`BoundColumn`
    objects. It provides methods that make accessing columns easier than if
    they were stored in a ``list`` or ``dict``. :class:`Columns` has a similar
    API to a ``dict`` (it actually uses a :class:`SortedDict` interally).

    At the moment you'll only come across this class when you access a
    :attr:`Table.columns` property.

    """
    def __init__(self, table):
        """Initialise a :class:`Columns` object.

        *table* must be a :class:`Table` object.

        """
        self.table = table
        # ``self._columns`` attribute stores the bound columns (columns that
        # have a real name, )
        self._columns = SortedDict()

    def _spawn_columns(self):
        # (re)build the "_columns" cache of BoundColumn objects (note that
        # ``base_columns`` might have changed since last time); creating
        # BoundColumn instances can be costly, so we reuse existing ones.
        new_columns = SortedDict()
        for name, column in self.table.base_columns.items():
            if name in self._columns:
                new_columns[name] = self._columns[name]
            else:
                new_columns[name] = BoundColumn(self.table, column, name)
        self._columns = new_columns

    def all(self):
        """Iterate through all :class:`BoundColumn` objects, regardless of
        visiblity or sortability.

        """
        self._spawn_columns()
        for column in self._columns.values():
            yield column

    def items(self):
        """Return an iterator of ``(name, column)`` pairs (where *column* is a
        :class:`BoundColumn` object).

        """
        self._spawn_columns()
        for r in self._columns.items():
            yield r

    def names(self):
        """Return an iterator of column names."""
        self._spawn_columns()
        for r in self._columns.keys():
            yield r

    def sortable(self):
        """Same as :meth:`all` but only returns sortable :class:`BoundColumn`
        objects.

        This is useful in templates, where iterating over the full
        set and checking ``{% if column.sortable %}`` can be problematic in
        conjunction with e.g. ``{{ forloop.last }}`` (the last column might not
        be the actual last that is rendered).

        """
        for column in self.all():
            if column.sortable:
                yield column

    def visible(self):
        """Same as :meth:`sortable` but only returns visible
        :class:`BoundColumn` objects.

        This is geared towards table rendering.

        """
        for column in self.all():
            if column.visible:
                yield column

    def __iter__(self):
        """Convenience API with identical functionality to :meth:`visible`."""
        return self.visible()

    def __contains__(self, item):
        """Check if a column is contained within a :class:`Columns` object.

        *item* can either be a :class:`BoundColumn` object, or the name of a
        column.

        """
        self._spawn_columns()
        if isinstance(item, basestring):
            return item in self.names()
        else:
            return item in self.all()

    def __len__(self):
        """Return how many :class:`BoundColumn` objects are contained."""
        self._spawn_columns()
        return len([1 for c in self._columns.values() if c.visible])

    def __getitem__(self, index):
        """Retrieve a specific :class:`BoundColumn` object.

        *index* can either be 0-indexed or the name of a column

        .. code-block:: python

            columns['speed']  # returns a bound column with name 'speed'
            columns[0]        # returns the first column

        """
        self._spawn_columns()
        if isinstance(index, int):
            return self._columns.value_for_index(index)
        elif isinstance(index, basestring):
            return self._columns[index]
        else:
            raise TypeError('row indices must be integers or str, not %s' %
                            index.__class__.__name__)
