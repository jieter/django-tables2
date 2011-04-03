# -*- coding: utf8 -*-
import copy
from django.core.paginator import Paginator
from django.utils.datastructures import SortedDict
from django.http import Http404
from django.template.loader import get_template
from django.template import Context
from django.utils.encoding import StrAndUnicode
from .utils import OrderBy, OrderByTuple, Accessor, AttributeDict
from .rows import BoundRows, BoundRow
from .columns import BoundColumns, Column


QUERYSET_ACCESSOR_SEPARATOR = '__'

class TableData(object):
    """
    Exposes a consistent API for :term:`table data`. It currently supports a
    :class:`QuerySet`, or a :class:`list` of :class:`dict` objects.

    This class is used by :class:.Table` to wrap any
    input table data.

    """
    def __init__(self, data, table):
        from django.db.models.query import QuerySet
        if isinstance(data, QuerySet):
            self.queryset = data
        elif isinstance(data, list):
            self.list = data
        else:
            raise ValueError('data must be a list or QuerySet object, not %s'
                             % data.__class__.__name__)
        self._table = table

        # work with a copy of the data that has missing values populated with
        # defaults.
        if hasattr(self, 'list'):
            self.list = copy.copy(self.list)
            self._populate_missing_values(self.list)

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

    def _populate_missing_values(self, data):
        """
        Populates self._data with missing values based on the default value
        for each column. It will create new items in the dataset (not modify
        existing ones).

        """
        for i, item in enumerate(data):
            # add data that is missing from the source. we do this now
            # so that the column's ``default`` values can affect
            # sorting (even when callables are used)!
            #
            # This is a design decision - the alternative would be to
            # resolve the values when they are accessed, and either do
            # not support sorting them at all, or run the callables
            # during sorting.
            modified_item = None
            for bound_column in self._table.columns.all():
                # the following will be True if:
                # * the source does not provide a value for the column
                #   or the value is None
                # * the column did provide a data callable that
                #   returned None
                accessor = Accessor(bound_column.accessor)
                try:
                    if accessor.resolve(item) is None:  # may raise ValueError
                        raise ValueError('None values also need replacing')
                except ValueError:
                    if modified_item is None:
                        modified_item = copy.copy(item)
                    modified_item[accessor.bits[0]] = bound_column.default
            if modified_item is not None:
                data[i] = modified_item


    def __getitem__(self, index):
        return (self.list if hasattr(self, 'list') else self.queryset)[index]


class DeclarativeColumnsMetaclass(type):
    """
    Metaclass that converts Column attributes on the class to a dictionary
    called ``base_columns``, taking into account parent class ``base_columns``
    as well.

    """
    def __new__(cls, name, bases, attrs, parent_cols_from=None):
        """Ughhh document this :)

        """
        # extract declared columns
        columns = [(name, attrs.pop(name)) for name, column in attrs.items()
                                           if isinstance(column, Column)]
        columns.sort(lambda x, y: cmp(x[1].creation_counter,
                                      y[1].creation_counter))

        # If this class is subclassing other tables, add their fields as
        # well. Note that we loop over the bases in *reverse* - this is
        # necessary to preserve the correct order of columns.
        for base in bases[::-1]:
            cols_attr = (parent_cols_from if (parent_cols_from and
                                             hasattr(base, parent_cols_from))
                                          else 'base_columns')
            if hasattr(base, cols_attr):
                columns = getattr(base, cols_attr).items() + columns
        # Note that we are reusing an existing ``base_columns`` attribute.
        # This is because in certain inheritance cases (mixing normal and
        # ModelTables) this metaclass might be executed twice, and we need
        # to avoid overriding previous data (because we pop() from attrs,
        # the second time around columns might not be registered again).
        # An example would be:
        #    class MyNewTable(MyOldNonModelTable, tables.ModelTable): pass
        if not 'base_columns' in attrs:
            attrs['base_columns'] = SortedDict()
        attrs['base_columns'].update(SortedDict(columns))
        attrs['_meta'] = TableOptions(attrs.get('Meta', None))
        return type.__new__(cls, name, bases, attrs)


class TableOptions(object):
    """
    Extracts and exposes options for a :class:`.Table` from a ``class Meta``
    when the table is defined.
    """
    def __init__(self, options=None):
        """

        :param options: options for a table
        :type options: :class:`Meta` on a :class:`.Table`

        """
        super(TableOptions, self).__init__()
        self.sortable = getattr(options, 'sortable', None)
        order_by = getattr(options, 'order_by', ())
        if isinstance(order_by, basestring):
            order_by = (order_by, )
        self.order_by = OrderByTuple(order_by)
        self.attrs = AttributeDict(getattr(options, 'attrs', {}))


class Table(StrAndUnicode):
    """A collection of columns, plus their associated data rows.

    :type data: :class:`list` or :class:`QuerySet`
    :param data:
        The :term:`table data`.

    :param: :class:`tuple`-like or :class:`basestring`
    :param order_by:
        The description of how the table should be ordered. This allows the
        :attr:`.Table.Meta.order_by` option to be overridden.

    .. note::
        Unlike a :class:`Form`, tables are always bound to data.

    """
    __metaclass__ = DeclarativeColumnsMetaclass

    # this value is not the same as None. it means 'use the default sort
    # order', which may (or may not) be inherited from the table options.
    # None means 'do not sort the data', ignoring the default.
    DefaultOrder = type('DefaultSortType', (), {})()
    TableDataClass = TableData

    def __init__(self, data, order_by=DefaultOrder):
        self._rows = BoundRows(self)  # bound rows
        self._columns = BoundColumns(self)  # bound columns
        self._data = self.TableDataClass(data=data, table=self)

        # None is a valid order, so we must use DefaultOrder as a flag
        # to fall back to the table sort order.
        self.order_by = (self._meta.order_by if order_by is Table.DefaultOrder
                                             else order_by)

        # Make a copy so that modifying this will not touch the class
        # definition. Note that this is different from forms, where the
        # copy is made available in a ``fields`` attribute. See the
        # ``Table`` class docstring for more information.
        self.base_columns = copy.deepcopy(type(self).base_columns)

    def __unicode__(self):
        return self.as_html()

    @property
    def data(self):
        return self._data

    @property
    def order_by(self):
        return self._order_by

    @order_by.setter
    def order_by(self, value):
        """Order the rows of the table based columns. ``value`` must be a
        sequence of column names.
        """
        # accept both string and tuple instructions
        order_by = value.split(',') if isinstance(value, basestring) else value
        order_by = () if order_by is None else order_by
        new = []
        # validate, raise exception on failure
        for o in order_by:
            name = OrderBy(o).bare
            if name in self.columns and self.columns[name].sortable:
                new.append(o)
        order_by = OrderByTuple(new)
        self._order_by = order_by
        self._data.order_by(order_by)

    @property
    def rows(self):
        return self._rows

    @property
    def columns(self):
        return self._columns

    def as_html(self):
        """Render the table to a simple HTML table.

        The rendered table won't include pagination or sorting, as those
        features require a RequestContext. Use the ``render_table`` template
        tag (requires ``{% load django_tables %}``) if you require this extra
        functionality.

        """
        template = get_template('django_tables/basic_table.html')
        return template.render(Context({'table': self}))

    @property
    def attrs(self):
        """The attributes that should be applied to the ``<table>`` tag when
        rendering HTML.

        :returns: :class:`~.utils.AttributeDict` object.

        """
        return self._meta.attrs

    def paginate(self, klass=Paginator, page=1, *args, **kwargs):
        self.paginator = klass(self.rows, *args, **kwargs)
        try:
            self.page = self.paginator.page(page)
        except Exception as e:
            raise Http404(str(e))
