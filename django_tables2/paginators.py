from __future__ import unicode_literals

from django.core.paginator import EmptyPage, Page, PageNotAnInteger, Paginator
from django.utils.translation import ugettext as _


class LazyPaginator(Paginator):
    """
    Implement lazy pagination, preventing any count() queries.

    Usage with SingleTableView::

        class UserListView(SingleTableView):
            table_class = UserTable
            table_data = User.objects.all()
            table_pagination = {
                "klass": LazyPaginator
            }
    """

    def __init__(self, object_list, per_page, **kwargs):
        self._num_pages = None

        super(LazyPaginator, self).__init__(object_list, per_page, **kwargs)

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
        number = self.validate_number(number)
        bottom = (number - 1) * self.per_page
        top = bottom + self.per_page
        # Retrieve more objects to check if there is a next page.
        objects = list(self.object_list[bottom : top + self.orphans + 1])
        objects_count = len(objects)
        if objects_count > (self.per_page + self.orphans):
            # If another page is found, increase the total number of pages.
            self._num_pages = number + 1
            # In any case,  return only objects for this page.
            objects = objects[: self.per_page]
        elif (number != 1) and (objects_count <= self.orphans):
            raise EmptyPage(_("That page contains no results"))
        else:
            # This is the last page.
            self._num_pages = number
        return Page(objects, number, self)

    def _get_count(self):
        raise NotImplementedError

    count = property(_get_count)

    def _get_num_pages(self):
        return self._num_pages

    num_pages = property(_get_num_pages)

    def _get_page_range(self):
        raise NotImplementedError

    page_range = property(_get_page_range)
