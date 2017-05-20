django-tables2 - An app for creating HTML tables
------------------------------------------------

.. image:: https://badge.fury.io/py/django-tables2.svg
    :target: https://pypi.python.org/pypi/django-tables2
    :alt: Latest PyPI version

.. image:: https://travis-ci.org/bradleyayers/django-tables2.svg?branch=master
    :target: https://travis-ci.org/bradleyayers/django-tables2
    :alt: Travis CI

django-tables2 simplifies the task of turning sets of data into HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
`django.forms` does for HTML forms. e.g.

- `Available on pypi <https://pypi.python.org/pypi/django-tables2>`_
- Tested against currently supported versions of Django
  `and the python versions Django supports <https://docs.djangoproject.com/en/dev/faq/install/#what-python-version-can-i-use-with-django>`_
  (see `Travis CI <https://travis-ci.org/bradleyayers/django-tables2>`_)
- `Documentation on readthedocs.org <https://django-tables2.readthedocs.io/en/latest/>`_
- `Bug tracker <http://github.com/bradleyayers/django-tables2/issues>`_

Features:

- Any iterable can be a data-source, but special support for Django querysets is included.
- The builtin UI does not rely on JavaScript.
- Support for automatic table generation based on a Django model.
- Supports custom column functionality via subclassing.
- Pagination.
- Column based table sorting.
- Template tag to enable trivial rendering to HTML.
- Generic view mixin.

.. image:: https://cdn.rawgit.com/bradleyayers/django-tables2/1044316e/docs/img/example.png
    :alt: An example table rendered using django-tables2

.. image:: https://cdn.rawgit.com/bradleyayers/django-tables2/1044316e/docs/img/bootstrap.png
    :alt: An example table rendered using django-tables2 and bootstrap theme

.. image:: https://cdn.rawgit.com/bradleyayers/django-tables2/1044316e/docs/img/semantic.png
    :alt: An example table rendered using django-tables2 and semantic-ui theme

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
Check out the `documentation <https://django-tables2.readthedocs.io/en/latest/>`_ for more details.
