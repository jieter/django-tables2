# -*- coding: utf8 -*-
from attest import Tests
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from .environment import testing_environment
from .reporters import (AbstractReporter, PlainReporter, FancyReporter,
                        auto_reporter, XmlReporter, QuickFixReporter)


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
        """
        Wrapper around default __call__ method to perform common Django
        test set up. This means that user-defined Test Cases aren't required to
        include a call to super().setUp().
        """
        self._pre_setup()
        try:
            yield self.client_class()
        finally:
            self._post_teardown()


class TestContext(TestCase, TransactionTestContext):
    """
    Does basically the same as TransactionTestContext, but surrounds every
    test with a transaction, monkey-patches the real transaction management
    routines to do nothing, and rollsback the test transaction at the end of
    the test. You have to use TransactionTestContext, if you need transaction
    management inside a test.
    """
