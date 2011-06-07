# -*- coding: utf8 -*-
import copy
from django.core.paginator import Paginator
from django.utils.datastructures import SortedDict
from django.http import Http404
from django.template.loader import get_template
from django.template import Context
from django.utils.encoding import StrAndUnicode
from django.db.models.query import QuerySet
from itertools import chain
from .utils import OrderBy, OrderByTuple, Accessor, AttributeDict
from .rows import BoundRows, BoundRow
from .columns import BoundColumns, Column


QUERYSET_ACCESSOR_SEPARATOR = '__'


class Sequence(list):
    """
    Represents a column sequence, e.g. ("first_name", "...", "last_name")

    This is used to represent ``Table.Meta.sequence`` or the Table
    constructors's ``sequence`` keyword argument.

    The sequence must be a list of column names and is used to specify the
    order of the columns on a table. Optionally a "..." item can be inserted,
    which is treated as a *catch-all* for column names that aren't explicitly
    specified.
    """
    def expand(self, columns):
        """
        Expands the "..." item in the sequence into the appropriate column
        names that should be placed there.

        :raises: ``ValueError`` if the sequence is invalid for the columns.
        """
        # validation
        if self.count("...") > 1:
            raise ValueError("'...' must be used at most once in a sequence.")
        elif "..." in self:
            # Check for columns in the sequence that don't exist in *columns*
            extra = (set(self) - set(("...", ))).difference(columns)
            if extra:
                raise ValueError(u"sequence contains columns that do not exist"
                                 u" in the table. Remove '%s'."
                                 % "', '".join(extra))
        else:
            diff = set(self) ^ set(columns)
            if diff:
                raise ValueError(u"sequence does not match columns. Fix '%s' "
                                 u"or possibly add '...'." % "', '".join(diff))
        # everything looks good, let's expand the "..." item
        columns = columns[:]  # don't modify
        head = []
        tail = []
        target = head  # start by adding things to the head
        for name in self:
            if name == "...":
                # now we'll start adding elements to the tail
                target = tail
                continue
            else:
                target.append(columns.pop(columns.index(name)))
        self[:] = list(chain(head, columns, tail))


class TableData(object):
    """
    Exposes a consistent API for :term:`table data`. It currently supports a
    :class:`QuerySet`, or a :class:`list` of :class:`dict` objects.

    This class is used by :class:`.Table` to wrap any
    input table data.
    """
    def __init__(self, data, table):
        if isinstance(data, QuerySet):
            self.queryset = data
        elif isinstance(data, list):
            self.list = data[:]
        else:
            raise ValueError('data must be a list or QuerySet object, not %s'
                             % data.__class__.__name__)
        self._table = table

    def __len__(self):
        # Use the queryset count() method to get the length, instead of
        # loading all results into memory. This allows, for example,
        # smart paginators that use len() to perform better.
        return (self.queryset.count() if hasattr(self, 'queryset')
                                      else len(self.list))

    def order_by(self, order_by):
        """
        Order the data based on column names in the table.

        :param order_by: the ordering to apply
        :type order_by: an :class:`~.utils.OrderByTuple` object
        """
        # translate order_by to something suitable for this data
        order_by = self._translate_order_by(order_by)
        if hasattr(self, 'queryset'):
            # need to convert the '.' separators to '__' (filter syntax)
            order_by = [o.replace(Accessor.SEPARATOR,
                                  QUERYSET_ACCESSOR_SEPARATOR)
                        for o in order_by]
            self.queryset = self.queryset.order_by(*order_by)
        else:
            self.list.sort(cmp=order_by.cmp)

    def _translate_order_by(self, order_by):
        """Translate from column names to column accessors"""
        translated = []
        for name in order_by:
            # handle order prefix
            prefix, name = ((name[0], name[1:]) if name[0] == '-'
                                                else ('', name))
            # find the accessor name
            column = self._table.columns[name]
            translated.append(prefix + column.accessor)
        return OrderByTuple(translated)

    def __iter__(self):
        """
        for ... in ... default to using this. There's a bug in Django 1.3
        with indexing into querysets, so this side-steps that problem (as well
        as just being a better way to iterate).
        """
        return (self.list.__iter__() if hasattr(self, 'list')
                                     else self.queryset.__iter__())

    def __getitem__(self, index):
        """Forwards indexing accesses to underlying data"""
        return (self.list if hasattr(self, 'list') else self.queryset)[index]


class DeclarativeColumnsMetaclass(type):
    """
    Metaclass that converts Column attributes on the class to a dictionary
    called ``base_columns``, taking into account parent class ``base_columns``
    as well.
    """

    def __new__(cls, name, bases, attrs):

        attrs["_meta"] = opts = TableOptions(attrs.get("Meta", None))
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
        # Start with the parent columns
        attrs["base_columns"] = SortedDict(parent_columns)
        # Possibly add some generated columns based on a model
        if opts.model:
            extra = SortedDict(((f.name, Column()) for f in opts.model._meta.fields))
            attrs["base_columns"].update(extra)
        # Explicit columns override both parent and generated columns
        attrs["base_columns"].update(SortedDict(columns))
        # Apply any explicit exclude setting
        for ex in opts.exclude:
            if ex in attrs["base_columns"]:
                attrs["base_columns"].pop(ex)
        # Now reorder the columns based on explicit sequence
        if opts.sequence:
            opts.sequence.expand(attrs["base_columns"].keys())
            attrs["base_columns"] = SortedDict(((x, attrs["base_columns"][x]) for x in opts.sequence))
        return type.__new__(cls, name, bases, attrs)


class TableOptions(object):
    """
    Extracts and exposes options for a :class:`.Table` from a ``class Meta``
    when the table is defined.

    :param options: options for a table
    :type options: :class:`Meta` on a :class:`.Table`
    """

    def __init__(self, options=None):
        super(TableOptions, self).__init__()
        self.attrs = AttributeDict(getattr(options, "attrs", {}))
        self.empty_text = getattr(options, "empty_text", None)
        self.exclude = getattr(options, "exclude", ())
        order_by = getattr(options, "order_by", ())
        if isinstance(order_by, basestring):
            order_by = (order_by, )
        self.order_by = OrderByTuple(order_by)
        self.sequence = Sequence(getattr(options, "sequence", ()))
        self.sortable = getattr(options, "sortable", True)
        self.model = getattr(options, "model", None)


class Table(StrAndUnicode):
    """
    A collection of columns, plus their associated data rows.

    :type data:  ``list`` or ``QuerySet``
    :param data: The :term:`table data`.

    :type order_by: ``None``, ``tuple`` or ``string``
    :param order_by: sort the table based on these columns prior to display.
        (default :attr:`.Table.Meta.order_by`)

    :type sortable: ``bool``
    :param sortable: Enable/disable sorting on this table

    :type empty_text: ``string``
    :param empty_text: Empty text to render when the table has no data.
        (default :attr:`.Table.Meta.empty_text`)

    The ``order_by`` argument is optional and allows the table's
    ``Meta.order_by`` option to be overridden. If the ``order_by is None``
    the table's ``Meta.order_by`` will be used. If you want to disable a
    default ordering, simply use an empty ``tuple``, ``string``, or ``list``,
    e.g. ``Table(…, order_by='')``.


    Example:

    .. code-block:: python

        def obj_list(request):
            ...
            # If there's no ?sort=…, we don't want to fallback to
            # Table.Meta.order_by, thus we must not default to passing in None
            order_by = request.GET.get('sort', ())
            table = SimpleTable(data, order_by=order_by)
            ...
    """
    __metaclass__ = DeclarativeColumnsMetaclass
    TableDataClass = TableData

    def __init__(self, data, order_by=None, sortable=None, empty_text=None,
                 exclude=None, attrs=None, sequence=None):
        self._rows = BoundRows(self)
        self._columns = BoundColumns(self)
        self._data = self.TableDataClass(data=data, table=self)
        self.attrs = attrs
        self.empty_text = empty_text
        self.sortable = sortable
        # Make a copy so that modifying this will not touch the class
        # definition. Note that this is different from forms, where the
        # copy is made available in a ``fields`` attribute.
        self.base_columns = copy.deepcopy(self.__class__.base_columns)
        self.exclude = exclude or ()
        for ex in self.exclude:
            if ex in self.base_columns:
                self.base_columns.pop(ex)
        self.sequence = sequence
        if order_by is None:
            self.order_by = self._meta.order_by
        else:
            self.order_by = order_by

    @property
    def data(self):
        return self._data

    @property
    def order_by(self):
        return self._order_by

    @order_by.setter
    def order_by(self, value):
        """
        Order the rows of the table based columns. ``value`` must be a sequence
        of column names.
        """
        # accept string
        order_by = value.split(',') if isinstance(value, basestring) else value
        # accept None
        order_by = () if order_by is None else order_by
        new = []
        # everything's been converted to a iterable, accept iterable!
        for o in order_by:
            ob = OrderBy(o)
            name = ob.bare
            if name in self.columns and self.columns[name].sortable:
                new.append(ob)
        order_by = OrderByTuple(new)
        self._order_by = order_by
        self._data.order_by(order_by)

    @property
    def sequence(self):
        return (self._sequence if self._sequence is not None
                               else self._meta.sequence)

    @sequence.setter
    def sequence(self, value):
        if value:
            value = Sequence(value)
            value.expand(self.base_columns.keys())
        self._sequence = value

    @property
    def sortable(self):
        return (self._sortable if self._sortable is not None
                               else self._meta.sortable)

    @sortable.setter
    def sortable(self, value):
        self._sortable = value

    @property
    def empty_text(self):
        return (self._empty_text if self._empty_text is not None
                                 else self._meta.empty_text)

    @empty_text.setter
    def empty_text(self, value):
        self._empty_text = value

    @property
    def rows(self):
        return self._rows

    @property
    def columns(self):
        return self._columns

    def as_html(self):
        """
        Render the table to a simple HTML table.

        The rendered table won't include pagination or sorting, as those
        features require a RequestContext. Use the ``render_table`` template
        tag (requires ``{% load django_tables %}``) if you require this extra
        functionality.
        """
        template = get_template('django_tables/basic_table.html')
        return template.render(Context({'table': self}))

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

    def paginate(self, klass=Paginator, per_page=25, page=1, *args, **kwargs):
        self.paginator = klass(self.rows, per_page, *args, **kwargs)
        try:
            self.page = self.paginator.page(page)
        except Exception as e:
            raise Http404(str(e))
