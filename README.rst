django-tables2 - An app for creating HTML tables
------------------------------------------------

.. image:: https://img.shields.io/pypi/v/django_tables2.svg
    :target: https://crate.io/packages/django_tables2/
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

Example
-------

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

This example shows one of the simplest cases, but django-tables2 can do a lot
more! Check out the _documentation: http://django-tables2.readthedocs.org/en/latest/ for more details.

Running the tests
-----------------

With ``tox`` installed, you can run the test suite by typing ``tox``. It will take
care of installing the correct dependencies. During development, you might not
want to wait for the tests to run in all environments. In that case, use the ``-e``
argument to specify an environment:

``tox -e py27-1.9`` to run the tests in python 2.7 with Django 1.9.

To generate a html coverage report:

    PYTHONPATH=~/workspace/django-tables2 py.test -s --cov=django_tables2 --cov-report html


Building the documentation
--------------------------

If you want to build the docs from within a virtualenv, and Sphinx is installed
globally, use:

    make html SPHINXBUILD="python $(which sphinx-build)"


Publishing a release
--------------------

1. Bump the version in ``django-tables2/__init__.py``.
2. Update ``CHANGELOG.md``.
3. Create a tag ``git tag -a v1.0.6 -m 'tagging v1.0.6'``
4. Run ``python setup.py sdist upload --sign --identity=<your gpg identity>``.
