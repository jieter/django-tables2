# coding: utf-8
from __future__ import unicode_literals

import copy
from collections import OrderedDict

import six
from django import VERSION
from django.core.paginator import Paginator
from django.db.models.fields import FieldDoesNotExist
from django.template import RequestContext
from django.template.loader import get_template

from . import columns
from .config import RequestConfig
from .rows import BoundRows
from .utils import (Accessor, AttributeDict, OrderBy, OrderByTuple, Sequence,
                    cached_property, computed_values, segment)

QUERYSET_ACCESSOR_SEPARATOR = '__'


class TableData(object):
    """
    Exposes a consistent API for :term:`table data`.

    :param  data: iterable containing data for each row
    :type   data: `~django.db.query.QuerySet` or `list` of `dict`
    :param table: `.Table` object
    """
    def __init__(self, data, table):
        self.table = table
        # data may be a QuerySet-like objects with count() and order_by()
        if (hasattr(data, 'count') and callable(data.count) and
                hasattr(data, 'order_by') and callable(data.order_by)):
            self.queryset = data
        # otherwise it must be convertable to a list
        else:
            # do some light validation
            if hasattr(data, '__iter__') or (hasattr(data, '__len__') and hasattr(data, '__getitem__')):
                self.list = list(data)
            else:
                raise ValueError(
                    'data must be QuerySet-like (have count and '
                    'order_by) or support list(data) -- %s has '
                    'neither' % type(data).__name__
                )

    def __len__(self):
        if not hasattr(self, "_length"):
            # Use the queryset count() method to get the length, instead of
            # loading all results into memory. This allows, for example,
            # smart paginators that use len() to perform better.
            self._length = (
                self.queryset.count() if hasattr(self, 'queryset') else len(self.list)
            )
        return self._length

    @property
    def data(self):
        return self.queryset if hasattr(self, "queryset") else self.list

    @property
    def ordering(self):
        """
        Returns the list of order by aliases that are enforcing ordering on the
        data.

        If the data is unordered, an empty sequence is returned. If the
        ordering can not be determined, `None` is returned.

        This works by inspecting the actual underlying data. As such it's only
        supported for querysets.
        """
        if hasattr(self, "queryset"):
            aliases = {}
            for bound_column in self.table.columns:
                aliases[bound_column.order_by_alias] = bound_column.order_by
            try:
                return next(segment(self.queryset.query.order_by, aliases))
            except StopIteration:
                pass

    def order_by(self, aliases):
        """
        Order the data based on order by aliases (prefixed column names) in the
        table.

        :param aliases: optionally prefixed names of columns ('-' indicates
                        descending order) in order of significance with
                        regard to data ordering.
        :type  aliases: `~.utils.OrderByTuple`
        """
        accessors = []
        for alias in aliases:
            bound_column = self.table.columns[OrderBy(alias).bare]
            # bound_column.order_by reflects the current ordering applied to
            # the table. As such we need to check the current ordering on the
            # column and use the opposite if it doesn't match the alias prefix.
            if alias[0] != bound_column.order_by_alias[0]:
                accessors += bound_column.order_by.opposite
            else:
                accessors += bound_column.order_by
        if hasattr(self, "queryset"):
            translate = lambda accessor: accessor.replace(Accessor.SEPARATOR, QUERYSET_ACCESSOR_SEPARATOR)
            if accessors:
                self.queryset = self.queryset.order_by(*(translate(a) for a in accessors))
        else:
            self.list.sort(key=OrderByTuple(accessors).key)

    def __iter__(self):
        """
        for ... in ... default to using this. There's a bug in Django 1.3
        with indexing into querysets, so this side-steps that problem (as well
        as just being a better way to iterate).
        """
        return iter(self.data)

    def __getitem__(self, key):
        """
        Slicing returns a new `.TableData` instance, indexing returns a
        single record.
        """
        return self.data[key]

    @cached_property
    def verbose_name(self):
        """
        The full (singular) name for the data.

        Queryset data has its model's `~django.db.Model.Meta.verbose_name`
        honored. List data is checked for a ``verbose_name`` attribute, and
        falls back to using ``"item"``.
        """
        if hasattr(self, "queryset"):
            return self.queryset.model._meta.verbose_name
        return getattr(self.list, "verbose_name", "item")

    @cached_property
    def verbose_name_plural(self):
        """
        The full (plural) name of the data.

        This uses the same approach as `.verbose_name`.
        """
        if hasattr(self, "queryset"):
            return self.queryset.model._meta.verbose_name_plural
        return getattr(self.list, "verbose_name_plural", "items")


class DeclarativeColumnsMetaclass(type):
    """
    Metaclass that converts `.Column` objects defined on a class to the
    dictionary `.Table.base_columns`, taking into account parent class
    ``base_columns`` as well.
    """
    def __new__(mcs, name, bases, attrs):
        attrs["_meta"] = opts = TableOptions(attrs.get("Meta", None))
        # extract declared columns
        cols, remainder = [], {}
        for attr_name, attr in attrs.items():
            if isinstance(attr, columns.Column):
                cols.append((attr_name, attr))
            else:
                remainder[attr_name] = attr
        attrs = remainder

        cols.sort(key=lambda x: x[1].creation_counter)

        # If this class is subclassing other tables, add their fields as
        # well. Note that we loop over the bases in *reverse* - this is
        # necessary to preserve the correct order of columns.
        parent_columns = []
        for base in bases[::-1]:
            if hasattr(base, "base_columns"):
                parent_columns = list(base.base_columns.items()) + parent_columns
        # Start with the parent columns
        attrs["base_columns"] = OrderedDict(parent_columns)
        # Possibly add some generated columns based on a model
        if opts.model:
            extra = OrderedDict()
            # honor Table.Meta.fields, fallback to model._meta.fields
            if opts.fields:
                # Each item in opts.fields is the name of a model field or a
                # normal attribute on the model
                for field_name in opts.fields:
                    try:
                        field = opts.model._meta.get_field(field_name)
                    except FieldDoesNotExist:
                        extra[field_name] = columns.Column()
                    else:
                        extra[field_name] = columns.library.column_for_field(field)

            else:
                for field in opts.model._meta.fields:
                    extra[field.name] = columns.library.column_for_field(field)
            attrs["base_columns"].update(extra)

        # Explicit columns override both parent and generated columns
        attrs["base_columns"].update(OrderedDict(cols))
        # Apply any explicit exclude setting
        for exclusion in opts.exclude:
            if exclusion in attrs["base_columns"]:
                attrs["base_columns"].pop(exclusion)
        # Now reorder the columns based on explicit sequence
        if opts.sequence:
            opts.sequence.expand(attrs["base_columns"].keys())
            # Table's sequence defaults to sequence declared in Meta
            # attrs['_sequence'] = opts.sequence
            attrs["base_columns"] = OrderedDict(((x, attrs["base_columns"][x]) for x in opts.sequence))

        # set localize on columns
        for col_name in attrs["base_columns"].keys():
            localize_column = None
            if col_name in opts.localize:
                localize_column = True
            # unlocalize gets higher precedence
            if col_name in opts.unlocalize:
                localize_column = False

            if localize_column is not None:
                attrs["base_columns"][col_name].localize = localize_column

        return super(DeclarativeColumnsMetaclass, mcs).__new__(mcs, name, bases, attrs)


class TableOptions(object):
    """
    Extracts and exposes options for a `.Table` from a `.Table.Meta`
    when the table is defined. See `.Table` for documentation on the impact of
    variables in this class.

    :param options: options for a table
    :type  options: `.Table.Meta` on a `.Table`
    """
    # pylint: disable=R0902
    def __init__(self, options=None):
        super(TableOptions, self).__init__()
        self.attrs = AttributeDict(getattr(options, "attrs", {}))
        self.default = getattr(options, "default", "—")
        self.empty_text = getattr(options, "empty_text", None)
        self.fields = getattr(options, "fields", ())
        self.exclude = getattr(options, "exclude", ())
        order_by = getattr(options, "order_by", None)
        if isinstance(order_by, six.string_types):
            order_by = (order_by, )
        self.order_by = OrderByTuple(order_by) if order_by is not None else None
        self.order_by_field = getattr(options, "order_by_field", "sort")
        self.page_field = getattr(options, "page_field", "page")
        self.per_page = getattr(options, "per_page", 25)
        self.per_page_field = getattr(options, "per_page_field", "per_page")
        self.prefix = getattr(options, "prefix", "")
        self.show_header = getattr(options, "show_header", True)
        self.sequence = Sequence(getattr(options, "sequence", ()))
        self.orderable = getattr(options, "orderable", True)
        self.model = getattr(options, "model", None)
        self.template = getattr(options, "template", "django_tables2/table.html")
        self.localize = getattr(options, "localize", ())
        self.unlocalize = getattr(options, "unlocalize", ())


class TableBase(object):
    """
    A representation of a table.


    .. attribute:: attrs

        HTML attributes to add to the ``<table>`` tag.

        :type: `dict`

        When accessing the attribute, the value is always returned as an
        `.AttributeDict` to allow easily conversion to HTML.


    .. attribute:: columns

        The columns in the table.

        :type: `.BoundColumns`


    .. attribute:: default

        Text to render in empty cells (determined by `.Column.empty_values`,
        default `.Table.Meta.default`)

        :type: `unicode`


    .. attribute:: empty_text

        Empty text to render when the table has no data. (default
        `.Table.Meta.empty_text`)

        :type: `unicode`


    .. attribute:: exclude

        The names of columns that shouldn't be included in the table.

        :type: iterable of `unicode`


    .. attribute:: order_by_field

        If not `None`, defines the name of the *order by* querystring field.

        :type: `unicode`


    .. attribute:: page

        The current page in the context of pagination.

        Added during the call to `.Table.paginate`.


    .. attribute:: page_field

        If not `None`, defines the name of the *current page* querystring
        field.

        :type: `unicode`


    .. attribute:: paginator

        The current paginator for the table.

        Added during the call to `.Table.paginate`.


    .. attribute:: per_page_field

        If not `None`, defines the name of the *per page* querystring field.

        :type: `unicode`


    .. attribute:: show_header

        If `False`, the table will not have a header (`<thead>`), default
        value is `True`

        :type: `bool`



    .. attribute:: prefix

        A prefix for querystring fields to avoid name-clashes when using
        multiple tables on a single page.

        :type: `unicode`


    .. attribute:: rows

        The rows of the table (ignoring pagination).

        :type: `.BoundRows`


    .. attribute:: sequence

        The sequence/order of columns the columns (from left to right).

        :type: iterable

        Items in the sequence must be :term:`column names <column name>`, or
        ``"..."`` (string containing three periods). ``...`` can be used as a
        catch-all for columns that aren't specified.


    .. attribute:: orderable

        Enable/disable column ordering on this table

        :type: `bool`


    .. attribute:: template

        The template to render when using ``{% render_table %}`` (default
        ``"django_tables2/table.html"``)

        :type: `unicode`

    """
    TableDataClass = TableData

    def __init__(self, data, order_by=None, orderable=None, empty_text=None,
                 exclude=None, attrs=None, sequence=None, prefix=None,
                 order_by_field=None, page_field=None, per_page_field=None,
                 template=None, default=None, request=None, show_header=None):
        super(TableBase, self).__init__()
        self.exclude = exclude or ()
        self.sequence = sequence
        self.data = self.TableDataClass(data=data, table=self)
        if default is None:
            default = self._meta.default
        self.default = default
        self.rows = BoundRows(data=self.data, table=self)
        attrs = computed_values(attrs if attrs is not None else self._meta.attrs)
        self.attrs = AttributeDict(attrs)
        self.empty_text = empty_text if empty_text is not None else self._meta.empty_text
        self.orderable = orderable
        self.prefix = prefix
        self.order_by_field = order_by_field
        self.page_field = page_field
        self.per_page_field = per_page_field
        self.show_header = show_header
        # Make a copy so that modifying this will not touch the class
        # definition. Note that this is different from forms, where the
        # copy is made available in a ``fields`` attribute.
        self.base_columns = copy.deepcopy(type(self).base_columns)
        # Keep fully expanded ``sequence`` at _sequence so it's easily accessible
        # during render. The priority is as follows:
        # 1. sequence passed in as an argument
        # 2. sequence declared in ``Meta``
        # 3. sequence defaults to '...'
        if sequence is not None:
            self._sequence = Sequence(sequence)
            self._sequence.expand(self.base_columns.keys())
        elif self._meta.sequence:
            self._sequence = self._meta.sequence
        else:
            self._sequence = Sequence(tuple(self._meta.fields) + ('...', ))
            self._sequence.expand(self.base_columns.keys())
        self.columns = columns.BoundColumns(self)
        # `None` value for order_by means no order is specified. This means we
        # `shouldn't touch our data's ordering in any way. *However*
        # `table.order_by = None` means "remove any ordering from the data"
        # (it's equivalent to `table.order_by = ()`).
        if order_by is None and self._meta.order_by is not None:
            order_by = self._meta.order_by
        if order_by is None:
            self._order_by = None
            # If possible inspect the ordering on the data we were given and
            # update the table to reflect that.
            order_by = self.data.ordering
            if order_by is not None:
                self.order_by = order_by
        else:
            self.order_by = order_by
        self.template = template
        # If a request is passed, configure for request
        if request:
            RequestConfig(request).configure(self)

    def as_html(self, request):
        """
        Render the table to a simple HTML table, adding `request` to the context.
        """
        template = get_template(self.template)

        context = {'table': self}
        if VERSION < (1, 8):
            context = RequestContext(request, context)
        else:
            context['request'] = request

        return template.render(context)

    @property
    def attrs(self):
        return self._attrs

    @attrs.setter
    def attrs(self, value):
        self._attrs = value

    @property
    def show_header(self):
        return (self._show_header if self._show_header is not None
                else self._meta.show_header)

    @show_header.setter
    def show_header(self, value):
        self._show_header = value

    @property
    def empty_text(self):
        return self._empty_text

    @empty_text.setter
    def empty_text(self, value):
        self._empty_text = value

    @property
    def order_by(self):
        return self._order_by

    @order_by.setter
    def order_by(self, value):
        """
        Order the rows of the table based on columns.

        :param value: iterable of order by aliases.
        """
        # collapse empty values to ()
        order_by = () if not value else value
        # accept string
        order_by = order_by.split(',') if isinstance(order_by, six.string_types) else order_by
        valid = []
        # everything's been converted to a iterable, accept iterable!
        for alias in order_by:
            name = OrderBy(alias).bare
            if name in self.columns and self.columns[name].orderable:
                valid.append(alias)
        self._order_by = OrderByTuple(valid)
        self.data.order_by(self._order_by)

    @property
    def order_by_field(self):
        return (self._order_by_field if self._order_by_field is not None
                else self._meta.order_by_field)

    @order_by_field.setter
    def order_by_field(self, value):
        self._order_by_field = value

    @property
    def page_field(self):
        return (self._page_field if self._page_field is not None
                else self._meta.page_field)

    @page_field.setter
    def page_field(self, value):
        self._page_field = value

    def paginate(self, klass=Paginator, per_page=None, page=1, *args, **kwargs):
        """
        Paginates the table using a paginator and creates a ``page`` property
        containing information for the current page.

        :type     klass: Paginator class
        :param    klass: a paginator class to paginate the results
        :type  per_page: `int`
        :param per_page: how many records are displayed on each page
        :type      page: `int`
        :param     page: which page should be displayed.

        Extra arguments are passed to the paginator.

        Pagination exceptions (`~django.core.paginator.EmptyPage` and
        `~django.core.paginator.PageNotAnInteger`) may be raised from this
        method and should be handled by the caller.
        """
        per_page = per_page or self._meta.per_page
        self.paginator = klass(self.rows, per_page, *args, **kwargs)
        self.page = self.paginator.page(page)

    @property
    def per_page_field(self):
        return (self._per_page_field if self._per_page_field is not None
                else self._meta.per_page_field)

    @per_page_field.setter
    def per_page_field(self, value):
        self._per_page_field = value

    @property
    def prefix(self):
        return (self._prefix if self._prefix is not None
                else self._meta.prefix)

    @prefix.setter
    def prefix(self, value):
        self._prefix = value

    @property
    def prefixed_order_by_field(self):
        return "%s%s" % (self.prefix, self.order_by_field)

    @property
    def prefixed_page_field(self):
        return "%s%s" % (self.prefix, self.page_field)

    @property
    def prefixed_per_page_field(self):
        return "%s%s" % (self.prefix, self.per_page_field)

    @property
    def sequence(self):
        return self._sequence

    @sequence.setter
    def sequence(self, value):
        if value:
            value = Sequence(value)
            value.expand(self.base_columns.keys())
        self._sequence = value

    @property
    def orderable(self):
        if self._orderable is not None:
            return self._orderable
        else:
            return self._meta.orderable

    @orderable.setter
    def orderable(self, value):
        self._orderable = value

    @property
    def template(self):
        if self._template is not None:
            return self._template
        else:
            return self._meta.template

    @template.setter
    def template(self, value):
        self._template = value

# Python 2/3 compatible way to enable the metaclass
Table = DeclarativeColumnsMetaclass(str('Table'), (TableBase, ), {})
