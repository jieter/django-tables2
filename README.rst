django-attest
=============

Provides the same testing helper functionality as Django's
:class:`django.test.TestCase` wrapper of :class:`unittest.TestCase`.

`django_attest.TestContext` provides the same functionality as subclassing
`django.test.TestCase`, and `django_attest.TransactionTestContext` does the
same as `django.test.TransactionTestCase`.

Both contexts provide a `django.test.TestClient` object (normally accessed via
`self.client` in `django.test.TestCase` tests), which can be used to make
requests to views for testing.


Installation
============

1. Just run `python setup.py install` or `pip install <tar.gz>`.
2. You're done! (There's **no reason** to add it to your ``INSTALLED_APPS``)


Usage
=====

The functionality is implemented as a context for tests:

.. code-block:: python

    from attest import Tests
    from django_attest import TestContext

    tests = Tests()
    tests.context(TestContext())

    @tests.test
    def can_add(client):
        client.get('/some-url/')  # same as self.client


If you want to specify fixtures, urls, a client_class, or multi_db, simply pass
in these options when creating the :class:`django_tables.TestContext` object:

.. code-block:: python

    from attest import Tests
    from django_attest import TestContext

    tests = Tests()
    tests.context(TestContext(fixtures=['testdata.json'], urls='myapp.urls'))
