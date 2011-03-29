# -*- coding: utf8 -*-
from django.test import TestCase, TransactionTestCase
from django.test.testcases import connections_support_transactions, \
    disable_transaction_methods, restore_transaction_methods
from django.test.client import Client
from django.db import transaction, connections, DEFAULT_DB_ALIAS
from django.core.management import call_command


class TransactionTestContext(TransactionTestCase):
    __name__ = 'blah_bada_boom'
    client_class = getattr(TransactionTestCase, 'client_class', Client)

    def __init__(self, fixtures=None, urls=None, client_class=None,
                 multi_db=None):
        if fixtures:
            self.fixtures = fixtures
        if urls:
            self.urls = urls
        if client_class:
            self.client_class = client_class
        if multi_db:
            self.multi_db = multi_db

    def __call__(self):
        """Wrapper around default __call__ method to perform common Django
        test set up. This means that user-defined Test Cases aren't required to
        include a call to super().setUp().

        """
        self._pre_setup()
        yield self.client_class()
        self._post_teardown()


class TestContext(TransactionTestContext):
    """Does basically the same as TransactionTestContext, but surrounds every
    test with a transaction, monkey-patches the real transaction management
    routines to do nothing, and rollsback the test transaction at the end of
    the test. You have to use TransactionTestContext, if you need transaction
    management inside a test.

    """
    def _fixture_setup(self):
        if not connections_support_transactions():
            return super(TestContext, self)._fixture_setup()

        # If the test case has a multi_db=True flag, setup all databases.
        # Otherwise, just use default.
        if getattr(self, 'multi_db', False):
            databases = connections
        else:
            databases = [DEFAULT_DB_ALIAS]

        for db in databases:
            transaction.enter_transaction_management(using=db)
            transaction.managed(True, using=db)
        disable_transaction_methods()

        from django.contrib.sites.models import Site
        Site.objects.clear_cache()

        for db in databases:
            if hasattr(self, 'fixtures'):
                args = [self.fixtures]
                kwargs = {
                    'verbosity': 0,
                    'commit': False,
                    'database': db
                }
                call_command('loaddata', *args, **kwargs)

    def _fixture_teardown(self):
        if not connections_support_transactions():
            return super(TestContext, self)._fixture_teardown()

        # If the test case has a multi_db=True flag, teardown all databases.
        # Otherwise, just teardown default.
        if getattr(self, 'multi_db', False):
            databases = connections
        else:
            databases = [DEFAULT_DB_ALIAS]

        restore_transaction_methods()
        for db in databases:
            transaction.rollback(using=db)
            transaction.leave_transaction_management(using=db)
