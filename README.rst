django-tables2 - An app for creating HTML tables
------------------------------------------------

.. image:: https://badge.fury.io/py/django-tables2.svg
    :target: https://pypi.python.org/pypi/django-tables2
    :alt: Latest PyPI version

.. image:: https://travis-ci.org/bradleyayers/django-tables2.svg
    :target: https://travis-ci.org/bradleyayers/django-tables2
    :alt: Travis CI

django-tables2 simplifies the task of turning sets of data into HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
`django.forms` does for HTML forms. e.g.

.. image:: http://dl.dropbox.com/u/33499139/django-tables2/example.png
    :alt: An example table rendered using django-tables2

Its features include:

- Any iterable can be a data-source, but special support for Django querysets is included.
- The builtin UI does not rely on JavaScript.
- Support for automatic table generation based on a Django model.
- Supports custom column functionality via subclassing.
- Pagination.
- Column based table sorting.
- Template tag to enable trivial rendering to HTML.
- Generic view mixin.

- `Available on pypi <https://pypi.python.org/pypi/django-tables2>`_
- `Tested with python 2.7, 3.3, 3.4, 3.5 and Django 1.8, 1.9 <https://travis-ci.org/bradleyayers/django-tables2>`_
- `Documentation on readthedocs.org <http://django-tables2.readthedocs.org/en/latest/>`_

Example
-------

Start by adding ``django_tables2`` to your ``INSTALLED_APPS`` setting like this:

.. code:: python

        INSTALLED_APPS = (
            ...,
            'django_tables2',
        )

Creating a table for a model `Simple` is as simple as:

.. code:: python

    import django_tables2 as tables

    class SimpleTable(tables.Table):
        class Meta:
            model = Simple

This would then be used in a view:

.. code:: python

    def simple_list(request):
        queryset = Simple.objects.all()
        table = SimpleTable(queryset)
        return render(request, 'simple_list.html', {'table': table})

And finally in the template:

.. code::

    {% load django_tables2 %}
    {% render_table table %}

This example shows one of the simplest cases, but django-tables2 can do a lot more! 
Check out the _documentation: http://django-tables2.readthedocs.org/en/latest/ for more details.
