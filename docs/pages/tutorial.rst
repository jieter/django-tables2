Tutorial
~~~~~~~~

This is a step-by-step guide to learn how to install and use django-tables2.

1. ``pip install django-tables2``
2. Add ``'django_tables2'`` to ``INSTALLED_APPS``
3. Add ``'django.template.context_processors.request'`` to the ``context_processors`` in your template setting ``OPTIONS``.


We are going to run through creating a tutorial app. Let's start with a simple model::

    # tutorial/models.py
    class Person(models.Model):
        name = models.CharField(verbose_name="full name")

Add some data so you have something to display in the table. Now write a view
to pass a ``Person`` queryset into a template::

    # tutorial/views.py
    from django.shortcuts import render

    def people(request):
        return render(request, 'people.html', {'people': Person.objects.all()})

Finally, implement the template::

    {# tutorial/templates/people.html #}
    {% load render_table from django_tables2 %}
    {% load static %}
    <!doctype html>
    <html>
        <head>
            <link rel="stylesheet" href="{% static 'django_tables2/themes/paleblue/css/screen.css' %}" />
        </head>
        <body>
            {% render_table people %}
        </body>
    </html>

Hook the view up in your URLs, and load the page, you should see:

.. figure:: /_static/tutorial.png
    :align: center
    :alt: An example table rendered using django-tables2

While simple, passing a queryset directly to ``{% render_table %}`` doesn't
allow for any customisation. For that, you must define a custom `.Table` class::

    # tutorial/tables.py
    import django_tables2 as tables
    from .models import Person

    class PersonTable(tables.Table):
        class Meta:
            model = Person
            # add class="paleblue" to <table> tag
            attrs = {'class': 'paleblue'}


You'll then need to instantiate and configure the table in the view, before
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
table instance:

.. sourcecode:: django

    {% render_table table %}

At this point you haven't actually customised anything, you've merely added the
boilerplate code that ``{% render_table %}`` does for you when given a
``QuerySet``. The remaining sections in this document describe how to change
various aspects of the table.

TODO: insert links to various customisation options here.
