.. _pagination:

Pagination
==========

Pagination is easy, just call :meth:`.Table.paginate` and pass in the current
page number::

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        table.paginate(page=request.GET.get("page", 1), per_page=25)
        return render(request, "people_listing.html", {"table": table})

If you are using `.RequestConfig`, pass pagination options to the constructor::

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        RequestConfig(request, paginate={"per_page": 25}).configure(table)
        return render(request, "people_listing.html", {"table": table})

If you are using `SingleTableView`, the table will get paginated by default::

    class PeopleListView(SingleTableView):
        table_class = PeopleTable

You can control the max number of page buttons rendered with `DJANGO_TABLES2_PAGE_RANGE` 
in your settings.py::

    DJANGO_TABLES2_PAGE_RANGE = 10

The default value of 10, in a table with 101 pages, would render 
`1, 2, 3, 4, 5, 6, 7, 8, ..., 101` on page 1 of the table for example.

Disabling pagination
~~~~~~~~~~~~~~~~~~~~

If you are using `SingleTableView` and want to disable the default behavior,
set `SingleTableView.table_pagination = False`

Lazy pagination
~~~~~~~~~~~~~~~

The default `~django.core.paginators.Paginator` wants to count the number of items,
which might be an expensive operation for large QuerySets.
In those cases, you can use `.LazyPaginator`, which does not perform a count,
but also does not know what the total amount of pages will be, until you've hit
the last page.

The `.LazyPaginator` does this by fetching `n + 1` records where the number of records
per page is `n`. If it receives `n` or less records, it knows it is on the last page,
preventing rendering of the 'next' button and further "..." ellipsis.
Usage with `SingleTableView`::

    class UserListView(SingleTableView):
        table_class = UserTable
        table_data = User.objects.all()
        paginator_class = LazyPaginator
