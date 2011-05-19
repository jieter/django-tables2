django-attest
=============

Provides the same testing helper functionality as Django's
``django.test.TestCase`` wrapper of ``unittest.TestCase``.

``django_attest.TestContext`` provides the same functionality as subclassing
``django.test.TestCase``, and ``django_attest.TransactionTestContext`` does the
same as ``django.test.TransactionTestCase``.

Both contexts provide a ``django.test.TestClient`` object (normally accessed
via ``self.client`` in ``django.test.TestCase`` tests), which can be used to
make requests to views for testing.


Installation
============

You have two options:

- Install from PyPI: ``python setup.py install``
- Download the source and ``pip install <tar.gz>``


Usage
=====

Create a test collection and include one of ``django-attest``'s test contexts.
The result is that a ``client`` argument is passed to each test within the
collection. ``client`` is a ``django.test.TestClient`` object and allows you to
make HTTP requests to your project.

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
in these options when creating the ``django_tables.TestContext`` object:

::

    from attest import Tests
    from django_attest import TestContext

    tests = Tests()
    tests.context(TestContext(fixtures=['testdata.json'], urls='myapp.urls'))


Test database
-------------

As mentioned above, if you want the same functionality as
``django.test.TransactionTestCase`` (i.e. transaction is rolled back after each
test), use ``TransactionTestContext`` rather than ``TestContext``, e.g.::

    from attest import Tests
    from django-attest import TransactionTestContext

    tests = Tests()
    tests.context(TransactionTestContext())

    @tests.test
    def some_test(client):
        # test something
        ...

If you're testing a reusable Django app you'll probably be using Attest's test
loader in your ``setup.py``. Example::

    from setuptools import setup, find_packages

    setup(
        ...
        tests_require=['Django >=1.1', 'Attest >=0.4', 'django-attest'],
        test_loader='attest:FancyReporter.test_loader',
        test_suite='tests.everything',
    )

In this example ``tests.everything`` is a test collection that contains all the
tests for the app, and ``attest:FancyReporter.test_loader`` is Attest's
standard test loader.

Testing a reusable Django app
-----------------------------

This is all good, but in order to use ``TransactionTestContext``, Django's
database infrastructure must be configured. Normally this is performed by
Django's test loader and a project's ``settings.py``, but since we're using
Attest's test loader and we don't have a project setup, database initialization
isn't performed automatically.

The solution is simple. In your ``tests/__init__.py`` file (or
where ever you're creating your master test collection) configure Django
settings, and use ``django.test.simple.DjangoTestSuiteRunner.setup_databases``
to perform the database initialization.

The following is from one of my reusable Django apps that uses
``django-attest`` (``django-tables``)::

    from attest import Tests, AssertImportHook
    from django.test.simple import DjangoTestSuiteRunner

    # django.utils.module_loading.module_has_submodule is busted in all
    # versions up to (and including) Django 1.3. It's important to do this
    # prior to loading ``django.conf``.
    AssertImportHook.disable()

    from django.conf import settings

    # It's important to configure prior to importing the tests, as some of them
    # import Django's DB stuff.
    settings.configure(
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        INSTALLED_APPS = [
            'tests.testapp',
            'django_tables',  # the app that this
        ],
        ROOT_URLCONF = 'tests.testapp.urls',
    )

    # The following
    runner = DjangoTestSuiteRunner()
    runner.setup_databases()

    from .templates import templates
    from .models import models

    everything = Tests([templates, models])

A few things to note:

- ``everything`` is the tests collection that contains all the separate test
  collections. The ``test_suite`` option in ``setup.py`` refers to this.
- ``INSTALLED_APPS`` contains ``tests.testapp`` which is a basic Django app
  inside the ``tests`` package that contains some URLs, models, and views that
  aid in testing.
- The database is *in-memory* and uses the ``django.db.backends.sqlite3``
  backend. This makes running the tests very simple as no database
  configuration is required by the developer.

Finally, the tests can be run via::

    python setup.py test
