# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.db.models.fields import FieldDoesNotExist
from django.utils.datastructures import SortedDict
from django.utils.safestring import SafeData
from django_tables2.templatetags.django_tables2 import title
from django_tables2.utils import A, AttributeDict, OrderBy, OrderByTuple
from itertools import ifilter, islice
import warnings


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

        :returns: column object of `None`
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

    `.Column` objects control the way a column (including the cells that
    fall within it) are rendered.


    .. attribute:: attrs

        HTML attributes for elements that make up the column.

        :type: `dict`

        This API is extended by subclasses to allow arbitrary HTML attributes
        to be added to the output.

        By default `.Column` supports:

        - *th* -- ``table/thead/th`` elements
        - *td* -- ``table/tbody/tr/td`` elements
        - *cell* -- fallback if *th* or *td* isn't defined


    .. attribute:: accessor

        An accessor that describes how to extract values for this column from
        the :term:`table data`.

        :type: `basestring` or `~.Accessor`


    .. attribute:: default

        The default value for the column. This can be a value or a callable
        object [1]_. If an object in the data provides `None` for a column, the
        default will be used instead.

        The default value may affect ordering, depending on the type of data
        the table is using. The only case where ordering is not affected is
        when a `.QuerySet` is used as the table data (since sorting is
        performed by the database).

        .. [1] The provided callable object must not expect to receive any
               arguments.


    .. attribute:: order_by

        Allows one or more accessors to be used for ordering rather than
        *accessor*.

        :type: `unicode`, `tuple`, `~.Accessor`


    .. attribute:: orderable

        If `False`, this column will not be allowed to influence row
        ordering/sorting.

        :type: `bool`


    .. attribute:: verbose_name

        A human readable version of the column name.

        :type: `unicode`

        This should not defined in title case, but rather natural case. It is
        converted to title case for use in column headers.


    .. attribute:: visible

        If `True`, this column will be included in the HTML output.

        :type: `bool`
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

        By default this titlises the `~.Column.verbose_name`. If
        `~.Column.verbose_name` is an instance of `~.safestring.SafeData`, it's
        used unmodified.

        :returns: `unicode` or `None`

        .. note::

            This property typically isn't accessed directly when a table is
            rendered. Instead, `.BoundColumn.header` is accessed which in turn
            accesses this property. This allows the header to fallback to the
            column name (it's only available on a `.BoundColumn` object hence
            accessing that first) when this property doesn't return something
            useful.
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

        This method can be overridden by :ref:`table.render_FOO` methods on the
        table or by subclassing `.Column`.

        :returns: `unicode`

        If the value for this cell is in `.empty_values`, this method is
        skipped and an appropriate default value is rendered instead.
        Subclasses should set `.empty_values` to ``()`` if they want to handle
        all values in `.render`.
        """
        return value

    @property
    def sortable(self):
        """
        *deprecated* -- use `.orderable` instead.
        """
        warnings.warn('`sortable` is deprecated, use `orderable` instead.',
                      DeprecationWarning)
        return self.orderable

    @classmethod
    def from_field(cls, field):
        """
        Return a specialised column for the model field or `None`.

        :param field: the field that needs a suitable column
        :type  field: model field instance
        :returns: `.Column` object or `None`

        If the column isn't specialised for the given model field, it should
        return `None`. This gives other columns the opportunity to do better.

        If the column is specialised, it should return an instance of itself
        that's configured appropriately for the field.
        """
        # Since this method is inherited by every subclass, only provide a
        # column if this class was asked directly.
        if cls is Column:
            return cls(verbose_name=field.verbose_name)


class BoundColumn(object):
    """
    A *run-time* version of `.Column`. The difference between
    `.BoundColumn` and `.Column`, is that `.BoundColumn` objects include the
    relationship between a `.Column` and a `.Table`. In practice, this
    means that a `.BoundColumn` knows the *"variable name"* given to the
    `.Column` when it was declared on the `.Table`.

    For convenience, all `.Column` properties are available from thisclass.

    :type   table: `.Table` object
    :param  table: the table in which this column exists
    :type  column: `.Column` object
    :param column: the type of column
    :type    name: `basestring` object
    :param   name: the variable name of the column used to when defining the
                   `.Table`. In this example the name is ``age``:

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
        Proxy to `.Column.attrs` but injects some values of our own.

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
        Returns an `.OrderByTuple` of appropriately prefixed data source
        keys used to sort this column.

        See `.order_by_alias` for details.
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
        Returns an `OrderBy` describing the current state of ordering for this
        column.

        The following attempts to explain the difference between `order_by`
        and `.order_by_alias`.

        `.order_by_alias` returns and `.OrderBy` instance that's based on
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

        The `OrderBy` returned has been patched to include an extra attribute
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
        Return a `bool` depending on whether this column supports ordering.
        """
        if self.column.orderable is not None:
            return self.column.orderable
        return self.table.orderable

    @property
    def verbose_name(self):
        """
        Return the verbose name for this column, or fallback to prettified
        column name.

        If the table is using queryset data, then use the corresponding model
        field's `~.db.Field.verbose_name`. If it's traversing a relationship,
        then get the last field in the accessor (i.e. stop when the
        relationship turns from ORM relationships to object attributes [e.g.
        person.upper should stop at person]).

        If the model field's `~.db.Field.verbose_name` is a
        `~.safestring.SafeData`, it's used unmodified.
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
        Returns a `bool` depending on whether this column is visible.
        """
        return self.column.visible


class BoundColumns(object):
    """
    Container for spawning `.BoundColumn` objects.

    This is bound to a table and provides its `.Table.columns` property.
    It provides access to those columns in different ways (iterator,
    item-based, filtered and unfiltered etc), stuff that would not be possible
    with a simple iterator in the table class.

    A `BoundColumns` object is a container for holding `BoundColumn` objects.
    It provides methods that make accessing columns easier than if they were
    stored in a `list` or `dict`. `Columns` has a similar API to a `dict` (it
    actually uses a `~django.utils.datastructures.SortedDict` interally).

    At the moment you'll only come across this class when you access a
    `.Table.columns` property.

    :type  table: `.Table` object
    :param table: the table containing the columns
    """
    def __init__(self, table):
        self.table = table
        self.columns = SortedDict()
        for name, column in table.base_columns.iteritems():
            self.columns[name] = bc = BoundColumn(table, column, name)
            bc.render = getattr(table, 'render_' + name, column.render)

    def iternames(self):
        return (name for name, column in self.iteritems())

    def names(self):
        return list(self.iternames())

    def iterall(self):
        """
        Return an iterator that exposes all `.BoundColumn` objects,
        regardless of visiblity or sortability.
        """
        return (column for name, column in self.iteritems())

    def all(self):
        return list(self.iterall())

    def iteritems(self):
        """
        Return an iterator of ``(name, column)`` pairs (where ``column`` is a
        `BoundColumn`).

        This method is the mechanism for retrieving columns that takes into
        consideration all of the ordering and filtering modifiers that a table
        supports (e.g. `~Table.Meta.exclude` and `~Table.Meta.sequence`).
        """
        for name in self.table.sequence:
            if name not in self.table.exclude:
                yield (name, self.columns[name])

    def items(self):
        return list(self.iteritems())

    def iterorderable(self):
        """
        Same as `BoundColumns.all` but only returns orderable columns.

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
        Same as `.iterorderable` but only returns visible `.BoundColumn`
        objects.

        This is geared towards table rendering.
        """
        return ifilter(lambda x: x.visible, self.iterall())

    def visible(self):
        return list(self.itervisible())

    def __iter__(self):
        """
        Convenience API, alias of `.itervisible`.
        """
        return self.itervisible()

    def __contains__(self, item):
        """
        Check if a column is contained within a `Columns` object.

        *item* can either be a `BoundColumn` object, or the name of a column.
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
        Retrieve a specific `BoundColumn` object.

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
