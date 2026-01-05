from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.paginator import EmptyPage, Page, PageNotAnInteger, Paginator
from django.utils.translation import gettext as _


class PageNumber(int):
    def __new__(cls, number, prefixed_page_field):
        self = super().__new__(cls, number)
        self._prefixed_page_field = prefixed_page_field
        return self

    @property
    def query(self):
        return {self._prefixed_page_field: str(self)}


class TablePaginatorMixin:
    def __init__(self, *args, **kwargs):
        table = kwargs.pop("table", None)
        super().__init__(*args, **kwargs)
        self.table = table
        self._prefixed_page_field = self.table.prefixed_page_field if self.table else "page"

    def previous_page_query(self):
        return {self._prefixed_page_field: self.table.page.previous_page_number()}

    def next_page_query(self):
        return {self._prefixed_page_field: self.table.page.next_page_number()}

    def page_query(self, page_number):
        return {self._prefixed_page_field: page_number}

    def table_page_range(self):
        """
        Return a list of max 10 (by default) page numbers.

        - always containing the first, last and current page.
        - containing one or two '...' to skip ranges between first/last and current.

        Example:
            {% for p in table.paginator.table_page_range %}
                {{ p }}
            {% endfor %}
        """
        if self.table is None:
            raise ImproperlyConfigured("table_page_range requires table to be set")

        page_range = getattr(settings, "DJANGO_TABLES2_PAGE_RANGE", 10)

        num_pages = self.num_pages
        if num_pages <= page_range:
            return [PageNumber(i, self._prefixed_page_field) for i in range(1, num_pages + 1)]

        range_start = self.table.page.number - int(page_range / 2)
        if range_start < 1:
            range_start = 1
        range_end = range_start + page_range
        if range_end > num_pages:
            range_start = num_pages - page_range + 1
            range_end = num_pages + 1

        ret = range(range_start, range_end)
        if 1 not in ret:
            ret = [1, Paginator.ELLIPSIS, *ret[2:]]
        if num_pages not in ret:
            ret = [*ret[:-2], Paginator.ELLIPSIS, num_pages]
        if isinstance(self, LazyPaginator) and not self.is_last_page(self.table.page.number):
            ret.append(Paginator.ELLIPSIS)
        return [PageNumber(i, self._prefixed_page_field) if isinstance(i, int) else i for i in ret]


class TablePaginator(TablePaginatorMixin, Paginator):
    pass


class LazyPaginator(Paginator):
    """
    Implement lazy pagination, preventing any count() queries.

    By default, for any valid page, the total number of pages for the paginator will be

     - `current + 1` if the number of records fetched for the current page offset is
       bigger than the number of records per page.
     - `current` if the number of records fetched is less than the number of records per page.

    The number of additional records fetched can be adjusted using `look_ahead`, which
    defaults to 1 page. If you like to provide a little more extra information on how much
    pages follow the current page, you can use a higher value.

    .. note::

        The number of records fetched for each page is `per_page * look_ahead + 1`, so increasing
        the value for `look_ahead` makes the view a bit more expensive.

    So::

        paginator = LazyPaginator(range(10000), 10)

        >>> paginator.page(1).object_list
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> paginator.num_pages
        2
        >>> paginator.page(10).object_list
        [91, 92, 93, 94, 95, 96, 97, 98, 99, 100]
        >>> paginator.num_pages
        11
        >>> paginator.page(1000).object_list
        [9991, 9992, 9993, 9994, 9995, 9996, 9997, 9998, 9999]
        >>> paginator.num_pages
        1000

    Usage with `~.SingleTableView`::

        class UserListView(SingleTableView):
            table_class = UserTable
            table_data = User.objects.all()
            pagination_class = LazyPaginator

    Or with `~.RequestConfig`::

        RequestConfig(paginate={"paginator_class": LazyPaginator}).configure(table)

    .. versionadded :: 2.0.0
    """

    look_ahead = 1

    def __init__(self, object_list, per_page, look_ahead=None, **kwargs):
        self._num_pages = None
        self._final_num_pages = None
        if look_ahead is not None:
            self.look_ahead = look_ahead

        super().__init__(object_list, per_page, **kwargs)

    def validate_number(self, number):
        """Validate the given 1-based page number."""
        try:
            if isinstance(number, float) and not number.is_integer():
                raise ValueError
            number = int(number)
        except (TypeError, ValueError):
            raise PageNotAnInteger(_("That page number is not an integer"))
        if number < 1:
            raise EmptyPage(_("That page number is less than 1"))
        return number

    def page(self, number):
        # Number might be None, because the total number of pages is not known in this paginator.
        # If an unknown page is requested, serve the first page.
        number = self.validate_number(number or 1)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        # Retrieve more objects to check if there is a next page.
        look_ahead_items = (self.look_ahead - 1) * self.per_page + 1
        objects = list(self.object_list[bottom : top + self.orphans + look_ahead_items])
        objects_count = len(objects)
        if objects_count > (self.per_page + self.orphans):
            # If another page is found, increase the total number of pages.
            self._num_pages = number + (objects_count // self.per_page)
            # In any case,  return only objects for this page.
            objects = objects[: self.per_page]
        elif (number != 1) and (objects_count <= self.orphans):
            raise EmptyPage(_("That page contains no results"))
        else:
            # This is the last page.
            self._num_pages = number
            # For rendering purposes in `table_page_range`, we have to remember the final count
            self._final_num_pages = number
        return Page(objects, number, self)

    def is_last_page(self, number):
        return number == self._final_num_pages

    def _get_count(self):
        raise NotImplementedError

    count = property(_get_count)

    def _get_num_pages(self):
        return self._num_pages

    num_pages = property(_get_num_pages)

    def _get_page_range(self):
        raise NotImplementedError

    page_range = property(_get_page_range)


class LazyTablePaginator(TablePaginatorMixin, LazyPaginator):
    pass
