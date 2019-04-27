from io import StringIO

import lxml.etree
import lxml.html
from django.core.handlers.wsgi import WSGIRequest
from django.test.client import FakePayload


def parse(html):
    # We use html instead of etree. Because etree can't parse html entities.
    return lxml.html.fromstring(html)


def attrs(xml):
    """
    Helper function that returns a dict of XML attributes, given an element.
    """
    return lxml.html.fromstring(xml).attrib


def build_request(uri="/", user=None):
    """
    Return a fresh HTTP GET / request.

    This is essentially a heavily cutdown version of Django's
    `~django.test.client.RequestFactory`.
    """
    path, _, querystring = uri.partition("?")
    request = WSGIRequest(
        {
            "CONTENT_TYPE": "text/html; charset=utf-8",
            "PATH_INFO": path,
            "QUERY_STRING": querystring,
            "REMOTE_ADDR": "127.0.0.1",
            "REQUEST_METHOD": "GET",
            "SCRIPT_NAME": "",
            "SERVER_NAME": "testserver",
            "SERVER_PORT": "80",
            "SERVER_PROTOCOL": "HTTP/1.1",
            "wsgi.version": (1, 0),
            "wsgi.url_scheme": "http",
            "wsgi.input": FakePayload(b""),
            "wsgi.errors": StringIO(),
            "wsgi.multiprocess": True,
            "wsgi.multithread": False,
            "wsgi.run_once": False,
        }
    )
    if user is not None:
        request.user = user
    return request
