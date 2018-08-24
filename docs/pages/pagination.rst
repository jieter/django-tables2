.. _pagination:

Pagination
==========

Pagination is easy, just call :meth:`.Table.paginate` and pass in the current
page number::

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        table.paginate(page=request.GET.get('page', 1), per_page=25)
        return render(request, 'people_listing.html', {'table': table})

If you are using `.RequestConfig`, pass pagination options to the constructor::

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        RequestConfig(request, paginate={'per_page': 25}).configure(table)
        return render(request, 'people_listing.html', {'table': table})

If you are using a class based view mixin, specify ``paginate_by`` in your class::

    class PeopleCBV(SingleTableView):
        paginate_by = 10


Lazy pagination
~~~~~~~~~~~~~~~

The default `~django.core.paginators.Paginator` want to count the number of items,
which might be an expensive operation for large QuerySets. In those cases, you can use
`.LazyPaginator`, which does not perform a count,
but also does not know what the total amount of pages will be.
It will always fetch the number of records for the page plus one.
If the number of records returned is equal to or smaller than the configured number of
records per page, it nows that the current page is the last page, and will make sure the
next button is not rendered.

Usage with `SingleTableView`::

    class UserListView(SingleTableView):
        table_class = UserTable
        table_data = User.objects.all()
        table_pagination = {
            "klass": LazyPaginator
        }
