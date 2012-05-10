from attest import assert_hook, Assert
import urlparse


class Assert(Assert):
    @staticmethod
    def redirects(response, url=None, scheme=None, domain=None, port=None,
                  path=None, query=None, fragment=None):
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
