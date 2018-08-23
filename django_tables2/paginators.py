from __future__ import unicode_literals

from django.core.paginator import EmptyPage, Page, PageNotAnInteger, Paginator
from django.utils.translation import ugettext as _


class CustomPage(Page):
    """Handle different number of items on the first page."""

    def start_index(self):
        """Return the 1-based index of the first item on this page."""
        paginator = self.paginator
        # Special case, return zero if no items.
        if paginator.count == 0:
            return 0
        elif self.number == 1:
            return 1
        return (self.number - 2) * paginator.per_page + paginator.first_page + 1

    def end_index(self):
        """Return the 1-based index of the last item on this page."""
        paginator = self.paginator
        # Special case for the last page because there can be orphans.
        if self.number == paginator.num_pages:
            return paginator.count
        return (self.number - 1) * paginator.per_page + paginator.first_page


class LazyPaginator(Paginator):
    """
    Implement lazy pagination.

    Handle different number of items on the first page.
    """

    def __init__(self, object_list, per_page, **kwargs):
        self._num_pages = None
        self.first_page = kwargs.pop("first_page", per_page)

        super(LazyPaginator, self).__init__(object_list, per_page, **kwargs)

    def get_current_per_page(self, number):
        return self.first_page if number == 1 else self.per_page

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
        current_per_page = self.get_current_per_page(number)
        if number == 1:
            bottom = 0
        else:
            bottom = (number - 2) * self.per_page + self.first_page
        top = bottom + current_per_page
        # Retrieve more objects to check if there is a next page.
        objects = list(self.object_list[bottom : top + self.orphans + 1])
        objects_count = len(objects)
        if objects_count > (current_per_page + self.orphans):
            # If another page is found, increase the total number of pages.
            self._num_pages = number + 1
            # In any case,  return only objects for this page.
            objects = objects[:current_per_page]
        elif (number != 1) and (objects_count <= self.orphans):
            raise EmptyPage("That page contains no results")
        else:
            # This is the last page.
            self._num_pages = number
        return CustomPage(objects, number, self)

    def _get_count(self):
        raise NotImplementedError

    count = property(_get_count)

    def _get_num_pages(self):
        return self._num_pages

    num_pages = property(_get_num_pages)

    def _get_page_range(self):
        raise NotImplementedError

    page_range = property(_get_page_range)
