from attest import assert_hook
from contextlib import contextmanager
from django.core.signals import request_started
from django.db import connections, DEFAULT_DB_ALIAS, reset_queries
import urlparse


__all__ = ("redirects", "queries")


def redirects(response, url=None, scheme=None, domain=None, port=None,
              path=None, query=None, fragment=None):
    """
    Given a Django response, asserts that it redirects to another URL, and that
    URL has various characteristics (e.g. response.path == "/foo").
    """
    assert response.status_code == 302
    if url:
        assert response["Location"] == url
    parts = urlparse.urlsplit(response["Location"])
    if scheme:
        assert parts.scheme == scheme
    if domain:
        assert parts.hostname == domain
    if port:
        assert parts.port == port
    if path:
        assert parts.path == path
    if query:
        assert parts.query == query
    if fragment:
        assert parts.fragment == fragment
    return True


@contextmanager
def queries(count=None, using=None):
    """
    A context manager that captures the queries that were made.

    :param count: assert this number of queries were made
    :param using: alias of the database to monitor

    .. note:: The `list` of queries is not populated until after the context
              manager exits.

    Usage::

        with queries() as qs:
            User.objects.count()
        assert len(qs) == 5

        # The same could be rewritten as
        with queries(count=5):
            User.objects.count()

    """
    if using is None:
        using = DEFAULT_DB_ALIAS
    conn = connections[using]
    # A debug cursor saves all the queries to conn.queries, in case one isn't
    # already being used, restore the current state after the test.
    was_debug_cursor = conn.use_debug_cursor
    conn.use_debug_cursor = True
    prior = len(conn.queries)
    executed = []
    request_started.disconnect(reset_queries)
    try:
        yield executed
    finally:
        request_started.connect(reset_queries)
        conn.use_debug_cursor = was_debug_cursor
    executed[:] = conn.queries[prior:]
    if count is not None:
        assert len(executed) == count
