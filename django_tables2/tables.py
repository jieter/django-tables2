# coding: utf-8
import copy
from django.conf import settings
from django.core.paginator import Paginator
from django.http import Http404
from django.utils.datastructures import SortedDict
from django.template import RequestContext
from django.template.loader import get_template
from django.utils.encoding import StrAndUnicode
import itertools
import sys
import warnings
from .utils import (Accessor, AttributeDict, OrderBy, OrderByTuple, segment,
                    Sequence)
from .rows import BoundRows
from .columns import BoundColumns, Column


QUERYSET_ACCESSOR_SEPARATOR = '__'


class TableData(object):
    """
    Exposes a consistent API for :term:`table data`.

    :param  data: iterable containing data for each row
    :type   data: :class:`QuerySet` or :class:`list` of :class:`dict`
    :param table: :class:`.Table` object
    """
    def __init__(self, data, table):
        self.table = table
        # data may be a QuerySet-like objects with count() and order_by()
        if (hasattr(data, 'count') and callable(data.count) and
            hasattr(data, 'order_by') and callable(data.order_by)):
            self.queryset = data
        # otherwise it must be convertable to a list
        else:
            try:
                self.list = list(data)
            except:
                raise ValueError('data must be QuerySet-like (have count and '
                                 'order_by) or support list(data) -- %s is '
                                 'neither' % type(data).__name__)

    def __len__(self):
        # Use the queryset count() method to get the length, instead of
        # loading all results into memory. This allows, for example,
        # smart paginators that use len() to perform better.
        return (self.queryset.count() if hasattr(self, 'queryset')
                                      else len(self.list))

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
            translate = lambda accessor: accessor.replace(QUERYSET_ACCESSOR_SEPARATOR, Accessor.SEPARATOR)
            for bound_column in self.table.columns:
                aliases[bound_column.order_by_alias] = bound_column.order_by
            try:
                return segment(self.queryset.query.order_by, aliases).next()
            except StopIteration:
                pass

    def order_by(self, aliases):
        """
        Order the data based on order by aliases (prefixed column names) in the
        table.

        :param aliases: optionally prefixed names of columns ('-' indicates
                        descending order) in order of significance with
                        regard to data ordering.
        :type  aliases: :class:`~.utils.OrderByTuple`
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
            self.queryset = self.queryset.order_by(*(translate(a) for a in accessors))
        else:
            self.list.sort(cmp=OrderByTuple(accessors).cmp)

    def __iter__(self):
        """
        for ... in ... default to using this. There's a bug in Django 1.3
        with indexing into querysets, so this side-steps that problem (as well
        as just being a better way to iterate).
        """
        return iter(self.list) if hasattr(self, 'list') else iter(self.queryset)

    def __getitem__(self, key):
        """
        Slicing returns a new :class:`.TableData` instance, indexing returns a
        single record.
        """
        data = (self.list if hasattr(self, 'list') else self.queryset)[key]
        if isinstance(key, slice):
            return type(self)(data, self.table)
        else:
            return data


class DeclarativeColumnsMetaclass(type):
    """
    Metaclass that converts Column attributes on the class to a dictionary
    called ``base_columns``, taking into account parent class ``base_columns``
    as well.
    """
    def __new__(cls, name, bases, attrs):

        opts = TableOptions(attrs.get("Meta", None))
        # extract declared columns
        columns = [(name_, attrs.pop(name_)) for name_, column in attrs.items()
                                             if isinstance(column, Column)]
        columns.sort(lambda x, y: cmp(x[1].creation_counter,
                                      y[1].creation_counter))

        # If this class is subclassing other tables, add their fields as
        # well. Note that we loop over the bases in *reverse* - this is
        # necessary to preserve the correct order of columns.
        parent_columns = []
        for base in bases[::-1]:
            if hasattr(base, "base_columns"):
                parent_columns = base.base_columns.items() + parent_columns

        # Pull in parent Meta options
        table_options = TableOptions()
        immediate_parent = bases[-1] # The immediate parent will already have the merged table options.
        if hasattr(immediate_parent, "_meta"):
            table_options.update(immediate_parent._meta)
            table_options.update(opts)
        else:
            table_options = opts
        attrs["_meta"] = opts = table_options

        # Start with the parent columns
        attrs["base_columns"] = SortedDict(parent_columns)
        # Possibly add some generated columns based on a model
        if opts.model:
            extra = SortedDict()
            for field in (opts.fields or opts.model._meta.fields):
                name = getattr(field, 'name', field)
                # We explicitly pass in verbose_name, so that if the table is
                # instantiated with non-queryset data, model field
                # verbose_names are used anyway.
                verbose_name = getattr(field, 'verbose_name', None)
                extra[name] = Column(verbose_name=verbose_name)

            attrs["base_columns"].update(extra)
        # Explicit columns override both parent and generated columns
        attrs["base_columns"].update(SortedDict(columns))
        # Apply any explicit exclude setting
        for exclusion in opts.exclude:
            if exclusion in attrs["base_columns"]:
                attrs["base_columns"].pop(exclusion)
        # Now reorder the columns based on explicit sequence
        if opts.sequence:
            opts.sequence.expand(attrs["base_columns"].keys())
            # Table's sequence defaults to sequence declared in Meta
            #attrs['_sequence'] = opts.sequence
            attrs["base_columns"] = SortedDict(((x, attrs["base_columns"][x]) for x in opts.sequence))
        return super(DeclarativeColumnsMetaclass, cls).__new__(cls, name, bases, attrs)


class TableOptions(object):
    """
    Extracts and exposes options for a :class:`.Table` from a ``class Meta``
    when the table is defined. See ``Table`` for documentation on the impact of
    variables in this class.

    :param options: options for a table
    :type  options: :class:`Meta` on a :class:`.Table`
    """
    def __init__(self, options=None):
        super(TableOptions, self).__init__()
        self._is_defaulted = []
        self.attrs = AttributeDict(getattr(options, "attrs", {}))
        self.default = getattr(options, "default", u"—")
        if getattr(options, "default", None) is None:
            self._is_defaulted.append('default')

        self.empty_text = getattr(options, "empty_text", None)
        self.fields = getattr(options, "fields", ())
        self.exclude = getattr(options, "exclude", ())
        order_by = getattr(options, "order_by", None)
        if isinstance(order_by, basestring):
            order_by = (order_by, )
        self.order_by = OrderByTuple(order_by) if order_by is not None else None
        self.order_by_field = getattr(options, "order_by_field", "sort")
        if getattr(options, "order_by_field", None) is None:
            self._is_defaulted.append('order_by_field')

        self.page_field = getattr(options, "page_field", "page")
        if getattr(options, "page_field", None) is None:
            self._is_defaulted.append('page_field')

        self.per_page = getattr(options, "per_page", 25)
        if getattr(options, "per_page", None) is None:
            self._is_defaulted.append('per_page')

        self.per_page_field = getattr(options, "per_page_field", "per_page")
        if getattr(options, "per_page_field", None) is None:
            self._is_defaulted.append('per_page_field')

        self.prefix = getattr(options, "prefix", "")
        if getattr(options, "prefix", None) is None:
            self._is_defaulted.append('prefix')

        self.sequence = Sequence(getattr(options, "sequence", ()))
        self._original_sequence = Sequence(self.sequence) # This to keep a non-expanded copy.

        if hasattr(options, "sortable"):
            warnings.warn("`Table.Meta.sortable` is deprecated, use `orderable` instead",
                          DeprecationWarning)
        self.orderable = self.sortable = getattr(options, "orderable", getattr(options, "sortable", True))
        if getattr(options, "orderable", getattr(options, "sortable", None)) is None:
            self._is_defaulted.append('orderable')

        self.model = getattr(options, "model", None)
        self.template = getattr(options, "template", "django_tables2/table.html")
        if getattr(options, "template", None) is None:
            self._is_defaulted.append('template')

    def update(self, table_option):
        self.attrs.update(table_option.attrs)
        if "default" not in table_option._is_defaulted:
            self.default = table_option.default
        if table_option.empty_text is not None:
            self.empty_text = table_option.empty_text
        self.fields += table_option.fields
        self.exclude += table_option.exclude
        if "order_by_field" not in table_option._is_defaulted:
            self.order_by_field = table_option.order_by_field
        if "page_field" not in table_option._is_defaulted:
            self.page_field = table_option.page_field
        if "prefix" not in table_option._is_defaulted:
            self.prefix = table_option.prefix
        if table_option._original_sequence:
            self._original_sequence = table_option._original_sequence
            self.sequence = Sequence(self._original_sequence)
        if "orderable" not in table_option._is_defaulted:
            self.orderable = self.sortable = table_option.orderable
        if table_option.model is not None:
            self.model = table_option.model
        if "template" not in table_option._is_defaulted:
            self.template = table_option.template

        if self.order_by is not None:
            if table_option.order_by is not None:
                self.order_by += table_option.order_by
        else:
            self.order_by = table_option.order_by


class Table(StrAndUnicode):
    """
    A collection of columns, plus their associated data rows.

    :type  attrs: dict
    :param attrs: A mapping of attributes to values that will be added to the
            HTML ``<table>`` tag.

    :type  data:  list or QuerySet-like
    :param data: The :term:`table data`.

    :type  exclude: iterable
    :param exclude: A list of columns to be excluded from this table.

    :type  order_by: None, tuple or string
    :param order_by: sort the table based on these columns prior to display.
            (default :attr:`.Table.Meta.order_by`)

    :type  order_by_field: string or None
    :param order_by_field: The name of the querystring field used to control
            the table ordering.

    :type  page_field: string or None
    :param page_field: The name of the querystring field used to control which
            page of the table is displayed (used when a table is paginated).

    :type  per_page_field: string or None
    :param per_page_field: The name of the querystring field used to control
            how many records are displayed on each page of the table.

    :type  prefix: string
    :param prefix: A prefix used on querystring arguments to allow multiple
            tables to be used on a single page, without having conflicts
            between querystring arguments. Depending on how the table is
            rendered, will determine how the prefix is used. For example ``{%
            render_table %}`` uses ``<prefix>-<argument>``.

    :type  sequence: iterable
    :param sequence: The sequence/order of columns the columns (from left to
            right). Items in the sequence must be column names, or the
            *remaining items* symbol marker ``"..."`` (string containing three
            periods). If this marker is used, not all columns need to be
            defined.

    :type  orderable: bool
    :param orderable: Enable/disable column ordering on this table

    :type  template: string
    :param template: the template to render when using {% render_table %}
            (default ``django_tables2/table.html``)

    :type  empty_text: string
    :param empty_text: Empty text to render when the table has no data.
            (default :attr:`.Table.Meta.empty_text`)

    :type  default: unicode
    :param default: Text to render in empty cells (determined by
            :attr:`Column.empty_values`, default :attrs:`.Table.Meta.default`)
    """
    __metaclass__ = DeclarativeColumnsMetaclass
    TableDataClass = TableData

    def __init__(self, data, order_by=None, orderable=None, empty_text=None,
                 exclude=None, attrs=None, sequence=None, prefix=None,
                 order_by_field=None, page_field=None, per_page_field=None,
                 template=None, sortable=None, default=None):
        super(Table, self).__init__()
        self.exclude = exclude or ()
        self.sequence = sequence
        self.data = self.TableDataClass(data=data, table=self)
        if default is None:
            default = self._meta.default
        self.default = default
        self.rows = BoundRows(self.data)
        self.attrs = attrs
        self.empty_text = empty_text
        if sortable is not None:
            warnings.warn("`sortable` is deprecated, use `orderable` instead.",
                          DeprecationWarning)
            if orderable is None:
                orderable = sortable
        self.orderable = orderable
        self.prefix = prefix
        self.order_by_field = order_by_field
        self.page_field = page_field
        self.per_page_field = per_page_field
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
            self._sequence = Sequence(self._meta.fields + ('...',))
            self._sequence.expand(self.base_columns.keys())
        self.columns = BoundColumns(self)
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

    def __unicode__(self):
        return unicode(repr(self))

    def as_html(self):
        """
        Render the table to a simple HTML table.

        If this method is used in the request/response cycle, any links
        generated will clobber the querystring of the request. Use the
        ``{% render_table %}`` template tag instead.
        """
        # minimizes Django 1.3 dependency
        from django.test.client import RequestFactory
        request = RequestFactory().get('/')
        template = get_template(self.template)
        return template.render(RequestContext(request, {'table': self}))

    def get_tr_attrs(self, record, bound_row):
        """
        Prepares the `AttributeDict` to be applied to the current row.

        This method can be overriden by sub-classes to customize the attributes
        (like 'class') applied to rows, on per row basis.

        The default implementation adds a 'class' attribute set to CSS class 'odd'
        or 'even' depnding on row's index. It gets the row index using `bound_row.key`.

        :param record: the model row from table data.
        :param bound_row: the bound_row instance from table.

        :rtype: :class:`~.utils.AttributeDict` object. Note that it is not `~.utils.Attrs`.
        """
        return AttributeDict({'class': 'even' if bound_row.key % 2 == 0 else 'odd'})

    @property
    def attrs(self):
        """
        The attributes that should be applied to the ``<table>`` tag when
        rendering HTML.

        :rtype: :class:`~.utils.AttributeDict` object.
        """
        return self._attrs if self._attrs is not None else self._meta.attrs

    @attrs.setter
    def attrs(self, value):
        self._attrs = value

    @property
    def empty_text(self):
        return (self._empty_text if self._empty_text is not None
                                 else self._meta.empty_text)

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
        order_by = order_by.split(',') if isinstance(order_by, basestring) else order_by
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

        :type     klass: Paginator ``class``
        :param    klass: a paginator class to paginate the results
        :type  per_page: ``int``
        :param per_page: how many records are displayed on each page
        :type      page: ``int``
        :param     page: which page should be displayed.
        """
        per_page = per_page or self._meta.per_page
        self.paginator = klass(self.rows, per_page, *args, **kwargs)
        self._page_number = page

    @property
    def page(self):
        if hasattr(self, '_page_number'):
            try:
                return self.paginator.page(self._page_number)
            except:
                if settings.DEBUG:
                    raise
                else:
                    raise Http404(sys.exc_info()[1])

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
        return u"%s%s" % (self.prefix, self.order_by_field)

    @property
    def prefixed_page_field(self):
        return u"%s%s" % (self.prefix, self.page_field)

    @property
    def prefixed_per_page_field(self):
        return u"%s%s" % (self.prefix, self.per_page_field)

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
        return (self._orderable if self._orderable is not None
                                else self._meta.orderable)

    @orderable.setter
    def orderable(self, value):
        self._orderable = value

    @property
    def sortable(self):
        warnings.warn("`sortable` is deprecated, use `orderable` instead.",
                      DeprecationWarning)
        return self.orderable

    @sortable.setter
    def sortable(self, value):
        warnings.warn("`sortable` is deprecated, use `orderable` instead.",
                      DeprecationWarning)
        self.orderable = value

    @property
    def template(self):
        return (self._template if self._template is not None
                               else self._meta.template)

    @template.setter
    def template(self, value):
        self._template = value
