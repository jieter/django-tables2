django-attest
=============

Django testing for Attest. Requires Django >=1.1.


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


Django assertions
-----------------

For details on each of these, see ``django_attest/assertion.py``.

redirects
^^^^^^^^^

Assert that a response redirects to some resource::

    from django_attest import redirects

    response = client.get('/')
    redirects(response, path="/foo/")


queries
^^^^^^^

Assert an expected set of queries took place::

    from django_attest import queries

    with queries() as qs:
        User.objects.count()
    assert len(qs) == 5

    # The same could be rewritten as
    with queries(count=5):
        User.objects.count()


Context managers
----------------

django-attest has some context managers to simplify common tasks:


settings
^^^^^^^^

Change global settings within a block, same functionality as Django 1.4's
``TestCase.settings``::

    from django_attest import settings

    with settings(MEDIA_ROOT="/tmp"):
        # ...

Code that's sensitive to settings changes should use the
``django_attest.signals.setting_changed`` signal to overcome any assumptions of
settings remaining constant.

.. note::

    On Django >=1.4, ``django_attest.signals.setting_changed`` is an alias of
    ``django.test.signals.setting_changed``.


urlconf
^^^^^^^

Takes a list of URL patterns and promotes them up as the root URLconf. This
avoids the need to have a dedicated *test project* and ``urls.py`` for simple
cases::

    @suite.test
    def foo(client):
        def view(request):
            return HttpResponse('success')

        urls = patterns('', (r'view/', view))
        with urlconf(urls):
            assert client.get(reverse(view)).content == 'success'

If you want to provide a dotted path to a ``urls.py``, use
``settings(ROOT_URLCONF=...)`` instead, it takes care to clear URL resolver
caches.


Backports
---------

- ``django_attest.RequestFactory`` (from Django 1.4)
- ``django_attest.settings`` (``override_settings`` inspired from Django 1.4)
