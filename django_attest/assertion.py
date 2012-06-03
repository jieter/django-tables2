from attest import assert_hook
import urlparse


__all__ = ("redirects", )


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
