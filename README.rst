django-attest
=============

Provides the same testing helper functionality as Django's
``django.test.TestCase`` wrapper of ``unittest.TestCase``.

``django_attest.TestContext`` provides the most of the same functionality as
subclassing ``django.test.TestCase``, and
``django_attest.TransactionTestContext`` does the same as
``django.test.TransactionTestCase``.

Both contexts provide a ``django.test.TestClient`` object (normally accessed
via ``self.client`` in ``django.test.TestCase`` tests), which can be used to
make requests to views for testing.


Installation
============

Use pip::

    pip install django-attest


Usage
=====

Create a test collection and optionally include one of ``django-attest``'s test
contexts. The result is that a ``client`` argument is passed to each test
within the collection. ``client`` is a ``django.test.TestClient`` object and
allows you to make HTTP requests to your project.

::

    from attest import Tests
    from django_attest import TestContext

    tests = Tests()
    tests.context(TestContext())

    @tests.test
    def can_add(client):
        client.get('/some-url/')  # same as self.client.get() if you were using
                                  # the standard django.test.TestCase approach

See the `TestCase.client documentation`__ for more details.

.. __: http://docs.djangoproject.com/en/1.3/topics/testing/#django.test.TestCase.client

When using a ``django.test.TestCase`` subclass, you're able to specify various
options that affect the environment in which your tests are executed.
``django-attest`` provides the same functionality via keyword arguments to the
``TestContext``. The following keyword arguments are supported:

- ``fixtures`` -- http://docs.djangoproject.com/en/1.3/topics/testing/#django.test.TestCase.fixtures
- ``urls`` -- http://docs.djangoproject.com/en/1.3/topics/testing/#django.test.TestCase.urls
- ``client_class`` -- http://docs.djangoproject.com/en/1.3/topics/testing/#django.test.TestCase.client_class
- ``multi_db`` -- http://docs.djangoproject.com/en/1.3/topics/testing/#django.test.TestCase.multi_db

For example if you want to specify fixtures, urls, a client_class,
or multi_db, simply pass
in these options when creating the ``django_tables.TestContext`` object::

    from attest import Tests
    from django_attest import TestContext

    tests = Tests()
    tests.context(TestContext(fixtures=['testdata.json'], urls='myapp.urls'))


Transaction management in tests
-------------------------------

If you need to test transaction management within your tests, use
``TransactionTestContext`` rather than ``TestContext``, e.g.::

    from attest import Tests
    from django_attest import TransactionTestContext

    tests = Tests()
    tests.context(TransactionTestContext())

    @tests.test
    def some_test(client):
        # test something
        ...

Testing a reusable Django app
-----------------------------

A flexible approach is to create a ``tests`` Django project. This shouldn't be
the fully-fledged output of ``django-admin.py startproject``, but instead the
minimum required to keep Django happy.


tests/__init__.py
^^^^^^^^^^^^^^^^^

::

    from attest import assert_hook, Tests
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.settings'
    from django_attest import auto_loader

    loader = autor_loader.test_loader
    suite = Tests()

    @suite.test
    def example():
        assert len("abc") == 3

Django's built-in test runner performs various environment initialisation and
cleanup tasks. It's important that tests are run using one of the loaders from
django-attest.


tests/settings.py
^^^^^^^^^^^^^^^^^

::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

    INSTALLED_APPS = [
        'django.contrib.sessions',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'my_reusable_app',
    ]

    SECRET_KEY = 'abcdefghiljklmnopqrstuvwxyz'

    ROOT_URLCONF = 'tests.urls'


tests/urls.py
^^^^^^^^^^^^^

::

    from django.conf.urls import patterns
    urlpatterns = patterns('')


setup.py
^^^^^^^^

::

    from setuptools import setup
    setup(
        ...
        tests_require=['Django >=1.1', 'Attest >=0.4', 'django-attest'],
        test_loader='tests:loader',
        test_suite='tests.suite',
    )


Running the tests
^^^^^^^^^^^^^^^^^

::

    python setup.py test


Testing non-reusable apps in a Django project
---------------------------------------------

To test non-reusable apps in a Django project, the app must contain either a
``tests`` or ``models`` module with either a ``suite`` function that returns a
``unittest.TestCase``, or simply contains ``TestCase`` classes. (see `Django's
documentation <http://docs.djangoproject.com/en/1.3/topics/testing/#writing-unit-tests>`_
for details).

As of Attest 0.6 you should use test cases::

    # myapp/tests.py
    from attest import Tests

    template = Tests()

    @template.test
    def filter():
        # ...

    template = template.test_case()

This allows Django to find your tests, and allows you to run individual tests,
e.g.::

    python manage.py test myapp.template.test_filter

.. note::

    When a ``unittest.TestCase`` is created from a test collection, the
    function names are prefixed with ``test_``.

Prior to Attest 0.6, you must use the test suite option, which unfortunately
doesn't support running individual tests::

    from attest import Tests

    template = Tests()

    @template.test
    def filter():
        # ...

    suite = template.test_suite


assert hook
-----------

Prior to Attest 0.5, the assert hook was enabled on first import of ``attest``.
As of Attest 0.6, this is no longer the case – instead it occurs when you use
the ``attest`` command line program to execute tests.

Since Django uses ``manage.py`` as its entry point, django-attest enables the
assert hook automatically when it's first imported.

This means that you need to do the following:

1. Make sure ``django_attest`` is imported as soon as possible.
2. Add ``from attest import assert_hook`` to the top of each test module.


Assert helper
-------------

Despite being deprecated in Attest 0.5, django-attest extends the ``Attest``
class to add helpers that are available in Django's ``TestCase`` class.

Example::

    from django_attest import Attest

    response = client.get('/')
    Attest.redirects(response, path="/foo/")

Have a look at the code for details.
