Filtering data in your table
============================

When presenting a large amount of data, filtering is often a necessity.
Fortunately, filtering the data in your django-tables2 table is simple with
`django-filter <https://pypi.python.org/pypi/django-filter>`_.

The basis of a filtered table is a `SingleTableMixin` combined with a
`FilterView` from django-filter::

    from django_filters.views import FilterView
    from django_tables2.views import SingleTableMixin


    class FilteredPersonListView(SingleTableMixin, FilterView):
        table_class = PersonTable
        model = Person
        template_name = 'template.html'

        filterset_class = PersonFilter


The filterset is added to the template context in a ``filter`` variable by
default. A basic template rendering it above the table looks like this::

    {% load render_table from django_tables2 %}
    {% load bootstrap3 %}

    {% if filter %}
        <form action="" method="get" class="form form-inline">
            {% bootstrap_form filter.form layout='inline' %}
            {% bootstrap_button 'filter' %}
        </form>
    {% endif %}
    {% render_table table 'django_tables2/bootstrap.html' %}
