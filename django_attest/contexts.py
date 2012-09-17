# coding: utf-8
from contextlib  import contextmanager
from django.conf import UserSettingsHolder
from django.test import Client, TestCase, TransactionTestCase
from .signals    import setting_changed


__all__ = ("settings", "TransactionTestContext", "TestContext")


class TransactionTestContext(TransactionTestCase):
    __name__ = 'blah_bada_boom'

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
            yield getattr(self, "client_class", Client)()
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


@contextmanager
def settings(**kwargs):
    """
    Change one or more Django settings.
    """
    from django.conf import settings
    original = settings._wrapped
    try:
        settings._wrapped = UserSettingsHolder(settings._wrapped)
        sender = type(settings._wrapped)
        for key, value in kwargs.items():
            setattr(settings._wrapped, key, value)
            setting_changed.send(sender=sender, setting=key, value=value)
        yield
    finally:
        settings._wrapped = original
        sender = type(settings._wrapped)
        for key, value in kwargs.items():
            value = getattr(settings, key, None)
            setting_changed.send(sender=sender, setting=key, value=value)
