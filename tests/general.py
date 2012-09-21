# coding: utf-8
from __future__ import absolute_import
import attest
from attest import assert_hook, AssertImportHook, COMPILES_AST, Tests
from contextlib import contextmanager
import django
try:
    from django.conf.urls import patterns
except ImportError:
    from django.conf.urls.defaults import patterns
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.test.client import Client
from django.test.simple import build_test
import django_attest
from django_attest import queries, redirects, TestContext, signals, urlconf
from pkg_resources import parse_version
from tests.app.models import Thing


suite = Tests()


@suite.test
def assert_import_hook_enabled_by_default():
    is_buggy_django = parse_version(django.get_version()) < parse_version('1.4')
    if not is_buggy_django and COMPILES_AST:
        assert AssertImportHook.enabled


@suite.test
def test_context_does_transaction_rollback():
    manager = contextmanager(TestContext())
    with manager():
        # create a thing, but it should be rolled back when the context exits
        thing = Thing.objects.create(name="foo")

    with attest.raises(Thing.DoesNotExist):
        Thing.objects.get(pk=thing.pk)


@suite.test
def test_context_supports_fixtures():
    with attest.raises(Thing.DoesNotExist):
        Thing.objects.get(name="loaded from fixture")

    manager = contextmanager(TestContext(fixtures=['tests']))
    with manager():
        Thing.objects.get(name="loaded from fixture")


@suite.test
def template_rendering_tracking_works():
    manager = contextmanager(TestContext())
    with manager() as client:
        response = client.get('/')
        assert response.content == "rendered from template.html\n"
        if hasattr(response, "templates"):
            # Django >= 1.3
            assert [t.name for t in response.templates] == ["template.html"]
        else:
            # Django <= 1.2
            assert response.template.name == "template.html"


@suite.test
def reporters():
    assert django_attest.auto_reporter.test_loader()
    assert django_attest.AbstractReporter.test_loader()
    assert django_attest.PlainReporter.test_loader()
    assert django_attest.FancyReporter.test_loader()
    assert django_attest.XmlReporter.test_loader()
    assert django_attest.QuickFixReporter.test_loader()


@suite.test_if(hasattr(Tests, "test_case"))
def testing_an_individual_test_via_managepy():
    from tests.app import tests
    assert tests.TEST_HAS_RUN == False
    test_suite = build_test("app.test_case.test_change_global")
    test_suite.debug()  # runs the tests
    assert tests.TEST_HAS_RUN == True


@suite.test
def assert_redirects():
    manager = contextmanager(TestContext())
    with manager() as client:
        response = client.get("/bouncer/")

    # First Django's API of passing the URL in by itself should work.
    redirects(response, "https://example.com:1234/foo/?a=b#bar")

    valids = [
        {"port": 1234},
        {"scheme": "https"},
        {"domain": "example.com"},
        {"query": "a=b"},
        {"path": "/foo/"},
        {"fragment": "bar"},
        {"url": "https://example.com:1234/foo/?a=b#bar"},
    ]

    for valid in valids:
        redirects(response, **valid)

    invalids = [
        {"port": 5678},
        {"scheme": "http"},
        {"domain": "example.net"},
        {"query": "c=d"},
        {"path": "/baz/"},
        {"fragment": "ben"},
        {"url": "http://example.net:5678/baz/?c=d#ben"},
    ]

    for invalid in invalids:
        with attest.raises(AssertionError):
            redirects(response, **invalid)


@suite.test
def assert_queries():
    with queries(count=1):
        list(Thing.objects.all())

    with queries(count=0):
        pass

    with queries() as qs:
        with queries(using='alternate') as others:
            list(Thing.objects.all())

    assert len(qs) == 1
    assert len(others) == 0


@suite.test
def changed_settings():
    from django.conf import settings
    sentinel = object()
    catcher = []  # use a list for scoping
    original = settings.DEBUG

    def pitcher(sender, setting, value, **kwargs):
        catcher.append({"setting": setting, "value": value})

    signals.setting_changed.connect(pitcher)

    with django_attest.settings(DEBUG=sentinel):
        assert settings.DEBUG is sentinel

    assert settings.DEBUG == original
    assert catcher == [{"setting": "DEBUG", "value": sentinel},
                       {"setting": "DEBUG", "value": original}]

    signals.setting_changed.disconnect(pitcher)


@suite.test
def urlconf_overrides_global():
    view = "tests.app.views.bouncer"
    assert reverse(view) == "/bouncer/"
    with urlconf(patterns("", (r'^outer/', view))):
        assert reverse(view) == "/outer/"
        with urlconf(patterns("", (r'^inner/', view))):
            assert reverse(view) == "/inner/"
        assert reverse(view) == "/outer/"
    assert reverse(view) == "/bouncer/"


@suite.test
def urlconf_allows_local_view():
    def view(request):
        return HttpResponse('success')

    client = Client()
    urls = patterns('', (r'view/', view))
    with urlconf(urls):
        assert client.get(reverse(view)).content == 'success'
