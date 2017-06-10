# coding: utf-8
from __future__ import absolute_import, unicode_literals

from collections import OrderedDict
from itertools import islice

from django.db import models
from django.utils import six
from django.utils.safestring import SafeData

from django_tables2.templatetags.django_tables2 import title
from django_tables2.utils import Accessor, AttributeDict, OrderBy, OrderByTuple, call_with_appropriate, computed_values


class Library(object):
    '''
    A collection of columns.
    '''
    def __init__(self):
        self.columns = []

    def register(self, column):
        self.columns.append(column)
        return column

    def column_for_field(self, field):
        '''
        Return a column object suitable for model field.

        Returns:
            `.Column` object or `None`
        '''
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
class Column(object):
    '''
    Represents a single column of a table.

    `.Column` objects control the way a column (including the cells that fall
    within it) are rendered.

    Arguments:
        attrs (dict): HTML attributes for elements that make up the column.
            This API is extended by subclasses to allow arbitrary HTML
            attributes to be added to the output.

            By default `.Column` supports:

             - *th* -- ``table/thead/tr/th`` elements
             - *td* -- ``table/tbody/tr/td`` elements
             - *cell* -- fallback if *th* or *td* isn't defined
        accessor (str or `~.Accessor`): An accessor that describes how to
            extract values for this column from the :term:`table data`.
        default (str or callable): The default value for the column. This can be
            a value or a callable object [1]_. If an object in the data provides
            `None` for a column, the default will be used instead.

            The default value may affect ordering, depending on the type of data
            the table is using. The only case where ordering is not affected is
            when a `.QuerySet` is used as the table data (since sorting is
            performed by the database).
        order_by (str, tuple or `.Accessor`): Allows one or more accessors to be
            used for ordering rather than *accessor*.
        orderable (bool): If `False`, this column will not be allowed to
            influence row ordering/sorting.
        verbose_name (str): A human readable version of the column name.
        visible (bool): If `True`, this column will be rendered.
        localize: If the cells in this column will be localized by the
            `localize` filter:

              - If `True`, force localization
              - If `False`, values are not localized
              - If `None` (default), localization depends on the ``USE_L10N`` setting.


    .. [1] The provided callable object must not expect to receive any arguments.
    '''
    # Tracks each time a Column instance is created. Used to retain order.
    creation_counter = 0
    empty_values = (None, '')

    # Explicit is set to True if the column is defined as an attribute of a
    # class, used to give explicit columns precedence.
    _explicit = False

    def __init__(self, verbose_name=None, accessor=None, default=None,
                 visible=True, orderable=None, attrs=None, order_by=None,
                 empty_values=None, localize=None, footer=None):
        if not (accessor is None or isinstance(accessor, six.string_types) or
                callable(accessor)):
            raise TypeError('accessor must be a string or callable, not %s' %
                            type(accessor).__name__)
        if callable(accessor) and default is not None:
            raise TypeError('accessor must be string when default is used, not callable')
        self.accessor = Accessor(accessor) if accessor else None
        self._default = default
        self.verbose_name = verbose_name
        self.visible = visible
        self.orderable = orderable
        self.attrs = attrs or {}
        # massage order_by into an OrderByTuple or None
        order_by = (order_by, ) if isinstance(order_by, six.string_types) else order_by
        self.order_by = OrderByTuple(order_by) if order_by is not None else None
        if empty_values is not None:
            self.empty_values = empty_values

        self.localize = localize

        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

        self._footer = footer

    @property
    def default(self):
        # handle callables
        return self._default() if callable(self._default) else self._default

    @property
    def header(self):
        '''
        The value used for the column heading (e.g. inside the ``<th>`` tag).

        By default this returns `~.Column.verbose_name`.

        :returns: `unicode` or `None`

        .. note::

            This property typically isn't accessed directly when a table is
            rendered. Instead, `.BoundColumn.header` is accessed which in turn
            accesses this property. This allows the header to fallback to the
            column name (it's only available on a `.BoundColumn` object hence
            accessing that first) when this property doesn't return something
            useful.
        '''
        return self.verbose_name

    def footer(self, bound_column, table):
        footer_kwargs = {
            'column': self,
            'bound_column': bound_column,
            'table': table
        }

        if self._footer is not None:
            if callable(self._footer):
                return call_with_appropriate(self._footer, footer_kwargs)
            else:
                return self._footer

        if hasattr(self, 'render_footer'):
            return call_with_appropriate(self.render_footer, footer_kwargs)

        return ''

    def render(self, value):
        '''
        Returns the content for a specific cell.

        This method can be overridden by :ref:`table.render_FOO` methods on the
        table or by subclassing `.Column`.

        :returns: `unicode`

        If the value for this cell is in `.empty_values`, this method is
        skipped and an appropriate default value is rendered instead.
        Subclasses should set `.empty_values` to ``()`` if they want to handle
        all values in `.render`.
        '''
        return value

    def value(self, **kwargs):
        '''
        Returns the content for a specific cell similarly to `.render` however
        without any html content. This can be used to get the data in the
        formatted as it is presented but in a form that could be added to a csv
        file.

        The default implementation just calls the `render` function but any
        subclasses where `render` returns html content should override this
        method.

        See `LinkColumn` for an example.
        '''
        value = call_with_appropriate(self.render, kwargs)

        # convert model instances to string, otherwise exporting to xls fails.
        if isinstance(value, models.Model):
            value = str(value)

        return value

    def order(self, queryset, is_descending):
        '''
        Returns the queryset of the table.

        This method can be overridden by :ref:`table.order_FOO` methods on the
        table or by subclassing `.Column`; but only overrides if second element
        in return tuple is True.

        returns:
            Tuple (queryset, boolean)
        '''
        return (queryset, False)

    @classmethod
    def from_field(cls, field):
        '''
        Return a specialised column for the model field or `None`.

        Arguments:
            field (Model Field instance): the field that needs a suitable column
        Returns:
            `.Column` object or `None`

        If the column isn't specialised for the given model field, it should
        return `None`. This gives other columns the opportunity to do better.

        If the column is specialised, it should return an instance of itself
        that's configured appropriately for the field.
        '''
        # Since this method is inherited by every subclass, only provide a
        # column if this class was asked directly.
        if cls is Column:
            if hasattr(field, 'get_related_field'):
                verbose_name = field.get_related_field().verbose_name
            else:
                verbose_name = getattr(field, 'verbose_name', field.name)
            return cls(verbose_name=title(verbose_name))


@six.python_2_unicode_compatible
class BoundColumn(object):
    '''
    A *run-time* version of `.Column`. The difference between
    `.BoundColumn` and `.Column`, is that `.BoundColumn` objects include the
    relationship between a `.Column` and a `.Table`. In practice, this
    means that a `.BoundColumn` knows the *"variable name"* given to the
    `.Column` when it was declared on the `.Table`.

    For convenience, all `.Column` properties are available from this class.

    arguments:
        table (`~.Table`): The table in which this column exists
        column (`~.Column`): The type of column
        name (str): The variable name of the column used when defining the
                    `.Table`. In this example the name is ``age``::

                          class SimpleTable(tables.Table):
                              age = tables.Column()

    '''
    def __init__(self, table, column, name):
        self._table = table
        self.column = column
        self.name = name

    def __str__(self):
        return six.text_type(self.header)

    @property
    def accessor(self):
        '''
        Returns the string used to access data for this column out of the data
        source.
        '''
        return self.column.accessor or Accessor(self.name)

    @property
    def attrs(self):
        '''
        Proxy to `.Column.attrs` but injects some values of our own.

        A ``th`` and ``td`` are guaranteed to be defined (irrespective of
        what's actually defined in the column attrs. This makes writing
        templates easier.
        '''
        # Start with table's attrs; Only 'th' and 'td' attributes will be used
        attrs = dict(self._table.attrs)

        # Update attrs to prefer column's attrs rather than table's
        attrs.update(dict(self.column.attrs))

        # we take the value for 'cell' as the basis for both the th and td attrs
        cell_attrs = attrs.get('cell', {})
        # override with attrs defined specifically for th and td respectively.
        kwargs = {
            'table': self._table
        }
        attrs['th'] = computed_values(attrs.get('th', cell_attrs), **kwargs)
        attrs['td'] = computed_values(attrs.get('td', cell_attrs), **kwargs)

        # wrap in AttributeDict
        attrs['th'] = AttributeDict(attrs['th'])
        attrs['td'] = AttributeDict(attrs['td'])

        # Override/add classes
        attrs['th']['class'] = self.get_th_class(attrs['th'])
        attrs['td']['class'] = self.get_td_class(attrs['td'])

        return attrs

    def get_td_class(self, td_attrs):
        '''
        Returns the HTML class attribute for a data cell in this column
        '''
        classes = set((c for c in td_attrs.get('class', '').split(' ') if c))
        classes = self._table.get_column_class_names(classes, self)
        return ' '.join(sorted(classes))

    def get_th_class(self, th_attrs):
        '''
        Returns the HTML class attribute for a header cell in this column
        '''
        classes = set((c for c in th_attrs.get('class', '').split(' ') if c))
        classes = self._table.get_column_class_names(classes, self)

        # add classes for ordering
        ordering_class = th_attrs.get('_ordering', {})
        if self.orderable:
            classes.add(ordering_class.get('orderable', 'orderable'))
        if self.is_ordered:
            classes.add(ordering_class.get('descending', 'desc')
                        if self.order_by_alias.is_descending
                        else ordering_class.get('ascending', 'asc'))

        return ' '.join(sorted(classes))

    @property
    def default(self):
        '''
        Returns the default value for this column.
        '''
        value = self.column.default
        if value is None:
            value = self._table.default
        return value

    @property
    def header(self):
        '''
        The value that should be used in the header cell for this column.
        '''
        # favour Column.header
        column_header = self.column.header
        if column_header:
            return column_header
        # fall back to automatic best guess
        return self.verbose_name

    @property
    def footer(self):
        return call_with_appropriate(self.column.footer, {
            'bound_column': self,
            'table': self._table
        })

    def has_footer(self):
        return self.column._footer is not None or hasattr(self.column, 'render_footer')

    @property
    def order_by(self):
        '''
        Returns an `.OrderByTuple` of appropriately prefixed data source
        keys used to sort this column.

        See `.order_by_alias` for details.
        '''
        if self.column.order_by is not None:
            order_by = self.column.order_by
        else:
            # default to using column accessor as data source sort key
            order_by = OrderByTuple((self.accessor, ))
        return order_by.opposite if self.order_by_alias.is_descending else order_by

    @property
    def order_by_alias(self):
        '''
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
            ...     name = tables.Column(order_by=('firstname', 'last_name'))
            ...
            >>> table = SimpleTable([], order_by=('-name', ))
            >>> table.columns['name'].order_by_alias
            '-name'
            >>> table.columns['name'].order_by
            ('-first_name', '-last_name')

        The `OrderBy` returned has been patched to include an extra attribute
        ``next``, which returns a version of the alias that would be
        transitioned to if the user toggles sorting on this column, e.g.::

            not sorted -> ascending
            ascending  -> descending
            descending -> ascending

        This is useful otherwise in templates you'd need something like::

            {% if column.is_ordered %}
            {% querystring table.prefixed_order_by_field=column.order_by_alias.opposite %}
            {% else %}
            {% querystring table.prefixed_order_by_field=column.order_by_alias %}
            {% endif %}

        '''
        order_by = OrderBy((self._table.order_by or {}).get(self.name, self.name))
        order_by.next = order_by.opposite if self.is_ordered else order_by
        return order_by

    @property
    def is_ordered(self):
        return self.name in (self._table.order_by or ())

    @property
    def orderable(self):
        '''
        Return a `bool` depending on whether this column supports ordering.
        '''
        if self.column.orderable is not None:
            return self.column.orderable
        return self._table.orderable

    @property
    def verbose_name(self):
        '''
        Return the verbose name for this column.

        In order of preference, this will return:
          1) The column's explicitly defined `verbose_name`
          2) The titlised model's `verbose_name` (if applicable)
          3) Fallback to the titlised column name.

        Any `verbose_name` that was not passed explicitly in the column
        definition is returned titlised in keeping with the Django convention
        of `verbose_name` being defined in lowercase and uppercased/titlised
        as needed by the application.

        If the table is using queryset data, then use the corresponding model
        field's `~.db.Field.verbose_name`. If it's traversing a relationship,
        then get the last field in the accessor (i.e. stop when the
        relationship turns from ORM relationships to object attributes [e.g.
        person.upper should stop at person]).
        '''
        # Favor an explicit defined verbose_name
        if self.column.verbose_name is not None:
            return self.column.verbose_name

        # This is our reasonable fallback, should the next section not result
        # in anything useful.
        name = self.name.replace('_', ' ')

        # Try to use a model field's verbose_name
        model = self._table.data.get_model()
        if model:
            field = Accessor(self.accessor).get_field(model)
            if field:
                if hasattr(field, 'field'):
                    name = field.field.verbose_name
                else:
                    name = getattr(field, 'verbose_name', field.name)

            # If verbose_name was mark_safe()'d, return intact to keep safety
            if isinstance(name, SafeData):
                return name

        return title(name)

    @property
    def visible(self):
        '''
        Returns a `bool` depending on whether this column is visible.
        '''
        return self.column.visible

    @property
    def localize(self):
        '''
        Returns `True`, `False` or `None` as described in ``Column.localize``
        '''
        return self.column.localize


class BoundColumns(object):
    '''
    Container for spawning `.BoundColumn` objects.

    This is bound to a table and provides its `.Table.columns` property.
    It provides access to those columns in different ways (iterator,
    item-based, filtered and unfiltered etc), stuff that would not be possible
    with a simple iterator in the table class.

    A `BoundColumns` object is a container for holding `BoundColumn` objects.
    It provides methods that make accessing columns easier than if they were
    stored in a `list` or `dict`. `Columns` has a similar API to a `dict` (it
    actually uses a `~collections.OrderedDict` interally).

    At the moment you'll only come across this class when you access a
    `.Table.columns` property.

    Arguments:
        table (`.Table`): the table containing the columns
    '''
    def __init__(self, table, base_columns):
        self._table = table
        self.columns = OrderedDict()
        for name, column in six.iteritems(base_columns):
            self.columns[name] = bc = BoundColumn(table, column, name)
            bc.render = getattr(table, 'render_' + name, column.render)
            bc.order = getattr(table, 'order_' + name, column.order)

    def iternames(self):
        return (name for name, column in self.iteritems())

    def names(self):
        return list(self.iternames())

    def iterall(self):
        '''
        Return an iterator that exposes all `.BoundColumn` objects,
        regardless of visiblity or sortability.
        '''
        return (column for name, column in self.iteritems())

    def all(self):
        return list(self.iterall())

    def iteritems(self):
        '''
        Return an iterator of ``(name, column)`` pairs (where ``column`` is a
        `BoundColumn`).

        This method is the mechanism for retrieving columns that takes into
        consideration all of the ordering and filtering modifiers that a table
        supports (e.g. `~Table.Meta.exclude` and `~Table.Meta.sequence`).
        '''

        for name in self._table.sequence:
            if name not in self._table.exclude:
                yield (name, self.columns[name])

    def items(self):
        return list(self.iteritems())

    def iterorderable(self):
        '''
        Same as `BoundColumns.all` but only returns orderable columns.

        This is useful in templates, where iterating over the full
        set and checking ``{% if column.ordarable %}`` can be problematic in
        conjunction with e.g. ``{{ forloop.last }}`` (the last column might not
        be the actual last that is rendered).
        '''
        return (x for x in self.iterall() if x.orderable)

    def orderable(self):
        return list(self.iterorderable())

    def itervisible(self):
        '''
        Same as `.iterorderable` but only returns visible `.BoundColumn`
        objects.

        This is geared towards table rendering.
        '''
        return (x for x in self.iterall() if x.visible)

    def visible(self):
        return list(self.itervisible())

    def hide(self, name):
        '''
        Hide a column.

        Arguments:
            name(str): name of the column
        '''
        self.columns[name].column.visible = False

    def show(self, name):
        '''
        Show a column otherwise hidden.

        Arguments:
            name(str): name of the column
        '''
        self.columns[name].column.visible = True

    def __iter__(self):
        '''
        Convenience API, alias of `.itervisible`.
        '''
        return self.itervisible()

    def __contains__(self, item):
        '''
        Check if a column is contained within a `Columns` object.

        *item* can either be a `~.BoundColumn` object, or the name of a column.
        '''
        if isinstance(item, six.string_types):
            return item in self.iternames()
        else:
            # let's assume we were given a column
            return item in self.iterall()

    def __len__(self):
        '''
        Return how many `~.BoundColumn` objects are contained (and
        visible).
        '''
        return len(self.visible())

    def __getitem__(self, index):
        '''
        Retrieve a specific `~.BoundColumn` object.

        *index* can either be 0-indexed or the name of a column

        .. code-block:: python

            columns['speed']  # returns a bound column with name 'speed'
            columns[0]        # returns the first column
        '''
        if isinstance(index, int):
            try:
                return next(islice(self.iterall(), index, index + 1))
            except StopIteration:
                raise IndexError
        elif isinstance(index, six.string_types):
            for column in self.iterall():
                if column.name == index:
                    return column
            raise KeyError("Column with name '%s' does not exist; "
                           "choices are: %s" % (index, self.names()))
        else:
            raise TypeError('Column indices must be integers or str, not %s'
                            % type(index).__name__)
