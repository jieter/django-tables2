Filtering data in your table
============================

When presenting a large amount of data, filtering is often a necessity.
Fortunately, filtering the data in your django-tables2 table is simple with
`django-filter <https://pypi.python.org/pypi/django-filter>`_.

The basis of a filterted table is a `SingleTableView` combined with a
`FilterView` from django-filter::

    from django_filters.views import FilterView


    class FilteredPersonListView(FilterView, SingleTableView):
        table_class = PersonTable
        model = Person
        template_name = 'template.html'

        filterset_class = PersonFilter
