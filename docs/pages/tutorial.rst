Tutorial
~~~~~~~~

This is a step-by-step guide to learn how to install and use django-tables2 using Django 1.11.

1. ``pip install django-tables2``
2. Start a new Django app using `python manage.py startapp tutorial`
3. Add both ``'django_tables2'`` and ``'tutorial'`` to your ``INSTALLED_APPS`` setting in ``settings.py``.

Now, add a model to your ``tutorial/models.py``::

    # tutorial/models.py
    class Person(models.Model):
        name = models.CharField(max_length=100, verbose_name='full name')

Create the database tables for the newly added model::

    $ python manage.py makemigrations tutorial
    $ python manage.py migrate tutorial

Add some data so you have something to display in the table::

    $ python manage.py shell
    >>> from tutorial.models import Person
    >>> Person.objects.bulk_create([Person(name='Jieter'), Person(name='Bradley')])
    [<Person: Person object>, <Person: Person object>]

Now write a view to pass a ``Person`` queryset into a template::

    # tutorial/views.py
    from django.shortcuts import render
    from .models import Person

    def people(request):
        return render(request, 'tutorial/people.html', {'people': Person.objects.all()})

Add the view to your ``urls.py``::

    # urls.py
    from django.conf.urls import url
    from django.contrib import admin

    from tutorial.views import people

    urlpatterns = [
        url(r'^admin/', admin.site.urls),
        url(r'^people/', people)
    ]

Finally, create the template::

    {# tutorial/templates/tutorial/people.html #}
    {% load render_table from django_tables2 %}
    <!doctype html>
    <html>
        <head>
            <title>List of persons</title>
        </head>
        <body>
            {% render_table people %}
        </body>
    </html>

You should be able to load the page in the browser (http://localhost:8000/people/ by default),
you should see:

.. figure:: /_static/tutorial.png
    :align: center
    :alt: An example table rendered using django-tables2

While simple, passing a queryset directly to ``{% render_table %}`` does not
allow for any customisation. For that, you must define a custom `.Table` class::

    # tutorial/tables.py
    import django_tables2 as tables
    from .models import Person

    class PersonTable(tables.Table):
        class Meta:
            model = Person
            template_name = 'django_tables2/bootstrap.html'


You will then need to instantiate and configure the table in the view, before
adding it to the context::

    # tutorial/views.py
    from django.shortcuts import render
    from django_tables2 import RequestConfig
    from .models import Person
    from .tables import PersonTable

    def people(request):
        table = PersonTable(Person.objects.all())
        RequestConfig(request).configure(table)
        return render(request, 'people.html', {'table': table})

Using `.RequestConfig` automatically pulls values from ``request.GET`` and
updates the table accordingly. This enables data ordering and pagination.

Rather than passing a queryset to ``{% render_table %}``, instead pass the
table instance::

    {# tutorial/templates/tutorial/people.html #}
    {% load render_table from django_tables2 %}
    <!doctype html>
    <html>
        <head>
            <title>List of persons</title>
            <link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css" />
        </head>
        <body>
            {% render_table table %}
        </body>
    </html>

This results in a table rendered with the bootstrap3 stylesheet:

.. figure:: /_static/tutorial-bootstrap.png
    :align: center
    :alt: An example table rendered using django-tables2 with the bootstrap template

At this point you have not actually customised anything but the template.
There are several topic you can read into to futher customize the table:

- Table data
    - :ref:`Populating the table with data <table_data>`,
    - :ref:`Filtering table data <filtering>`
- Custumizing the rendered table
    - :ref:`Headers and footers <column-headers-and-footers>`
    - :ref:`pinned_rows`
- :ref:`api-public`
