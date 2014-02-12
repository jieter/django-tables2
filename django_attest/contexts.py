# coding: utf-8
from contextlib  import contextmanager
from django.conf import settings, UserSettingsHolder
from django.test import Client, TestCase, TransactionTestCase
from .signals    import setting_changed


__all__ = ("settings", "TransactionTestContext", "TestContext", "translation",
           "urlconf")


class TransactionTestContext(TransactionTestCase):
    # Avoid this class from being treated as a TestCase by Django's collector
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
            setting_changed.send(sender=sender, setting=key, value=value,
                                 enter=True)
        yield
    finally:
        settings._wrapped = original
        sender = type(settings._wrapped)
        for key, value in kwargs.items():
            value = getattr(settings, key, None)
            setting_changed.send(sender=sender, setting=key, value=value,
                                 enter=False)


@contextmanager
def translation(language_code, deactivate=False):
    """
    Port of django.utils.translation.override from Django 1.4

    @param language_code: a language code or ``None``. If ``None``, translation
                          is disabled and raw translation strings are used
    @param    deactivate: If ``True``, when leaving the manager revert to the
                          default behaviour (i.e. ``settings.LANGUAGE_CODE``)
                          rather than the translation that was active prior to
                          entering.
    """
    from django.utils import translation
    original = translation.get_language()
    if language_code is not None:
        translation.activate(language_code)
    else:
        translation.deactivate_all()
    try:
        yield
    finally:
        if deactivate:
            translation.deactivate()
        else:
            translation.activate(original)


@contextmanager
def urlconf(patterns):
    """
    A context manager that turns URL patterns into the global URLconf.

    This is useful when you have a local variable of URL patterns that

    :param patterns: list of `RegexURLPattern` or `RegexURLResolver` (what you
                     get from `patterns`)

    .. note:: Not thread safe
    """
    NOTSET = object()
    global urlpatterns
    # The extravagent effort here to preserve the current value of urlpatterns
    # is done to ensure nesting of `urlconf`.
    try:
        old = urlpatterns
    except NameError:
        old = NOTSET
    urlpatterns = patterns
    try:
        with settings(ROOT_URLCONF=__name__):
            yield
    finally:
        if old is NOTSET:
            del urlpatterns
        else:
            urlpatterns = old
