.. _pagination:

Pagination
==========

Pagination is easy, just call :meth:`.Table.paginate` and pass in the current
page number::

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        table.paginate(page=request.GET.get('page', 1), per_page=25)
        return render(request, 'people_listing.html', {'table': table})

If you're using `.RequestConfig`, pass pagination options to the constructor::

    def people_listing(request):
        table = PeopleTable(Person.objects.all())
        RequestConfig(request, paginate={'per_page': 25}).configure(table)
        return render(request, 'people_listing.html', {'table': table})
