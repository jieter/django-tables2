# coding: utf-8
from contextlib import contextmanager
from functools  import wraps
import six
import sys


__all__ = ("contextdecorator", "nested", "RequestFactory")


def contextdecorator(yielder):
    """
    Given a function that returns a contextmanager style generator, return an
    object that can be used as a context for an Attest collection, or used to
    decorate an individual test.

    Usage::

        # Define the context/decorator
        @contextdecorator
        def database(port=5432):
            try:
                db.open(port)
                yield
            finally:
                db.close()

        # Can decorate functions...
        @database
        def foo():
            ...

        # and supports keyword arguments...
        @database(port=6543)
        def foo():
            ...

        # but can still be used with contextlib.contextmanager
        with contextmanager(database)():
            ...
        with contextmanager(database(port=6543))():
            ...

        # which means it can be used as a test collection context
        suite = Tests()
        suite.context(database)
        suite.context(database(port=6532))

    .. note::

        *yielder* arguments must be optional keywords.

    """
    @wraps(yielder)
    def thing(func=None, **kwargs):
        def wrap(func):
            # wrap func using yielder as a context manager
            @wraps(func)
            def wrapped():
                with contextmanager(yielder)(**kwargs):
                    return func()
            return wrapped

        if func:
            # @thing
            # def foo():
            #     ...
            return wrap(func)

        elif kwargs:
            @wraps(yielder)
            def wrapped(func=None):
                if func:
                    # @thing(foo='bar')
                    # def foo():
                    #     ...
                    return wrap(func)
                else:
                    # contextlib.contextmanager(thing(foo='bar'))
                    return yielder(**kwargs)
            return wrapped

        else:
            # contextlib.contextmanager(thing)
            return yielder()
    return thing


@contextmanager
def nested(*managers):
    exc = None, None, None
    args = []
    exits = []
    try:
        for manager in managers:
            args.append(manager.__enter__())
            exits.append(manager.__exit__)
        yield args
    except:
        exc = sys.exc_info()
    finally:
        for exit in reversed(exits):
            try:
                if exit(*exc):
                    exc = None, None, None
            except:
                exc = sys.exc_info()
        if exc != (None, None, None):
            six.reraise(*exc)


try:
    from django.test.client import RequestFactory
except ImportError:
    # Provide our own version, copied from Django 1.4
    from django.test.client import (
            BOUNDARY, CONTENT_TYPE_RE, encode_multipart, FakePayload,
            MULTIPART_CONTENT,  StringIO, SimpleCookie, smart_str, WSGIRequest,
            settings, urlencode, urllib, urlparse)

    class RequestFactory(object):
        def __init__(self, **defaults):
            self.defaults = defaults
            self.cookies = SimpleCookie()
            self.errors = StringIO()

        def _base_environ(self, **request):
            environ = {
                'HTTP_COOKIE':       self.cookies.output(header='', sep='; '),
                'PATH_INFO':         '/',
                'REMOTE_ADDR':       '127.0.0.1',
                'REQUEST_METHOD':    'GET',
                'SCRIPT_NAME':       '',
                'SERVER_NAME':       'testserver',
                'SERVER_PORT':       '80',
                'SERVER_PROTOCOL':   'HTTP/1.1',
                'wsgi.version':      (1, 0),
                'wsgi.url_scheme':   'http',
                'wsgi.input':        FakePayload(''),
                'wsgi.errors':       self.errors,
                'wsgi.multiprocess': True,
                'wsgi.multithread':  False,
                'wsgi.run_once':     False,
            }
            environ.update(self.defaults)
            environ.update(request)
            return environ

        def request(self, **request):
            return WSGIRequest(self._base_environ(**request))

        def _encode_data(self, data, content_type, ):
            if content_type is MULTIPART_CONTENT:
                return encode_multipart(BOUNDARY, data)
            else:
                # Encode the content so that the byte representation is correct.
                match = CONTENT_TYPE_RE.match(content_type)
                if match:
                    charset = match.group(1)
                else:
                    charset = settings.DEFAULT_CHARSET
                return smart_str(data, encoding=charset)

        def _get_path(self, parsed):
            # If there are parameters, add them
            if parsed[3]:
                return urllib.unquote(parsed[2] + ";" + parsed[3])
            else:
                return urllib.unquote(parsed[2])

        def get(self, path, data={}, **extra):
            parsed = urlparse(path)
            r = {
                'CONTENT_TYPE':    'text/html; charset=utf-8',
                'PATH_INFO':       self._get_path(parsed),
                'QUERY_STRING':    urlencode(data, doseq=True) or parsed[4],
                'REQUEST_METHOD': 'GET',
            }
            r.update(extra)
            return self.request(**r)

        def post(self, path, data={}, content_type=MULTIPART_CONTENT,
                 **extra):
            "Construct a POST request."

            post_data = self._encode_data(data, content_type)

            parsed = urlparse(path)
            r = {
                'CONTENT_LENGTH': len(post_data),
                'CONTENT_TYPE':   content_type,
                'PATH_INFO':      self._get_path(parsed),
                'QUERY_STRING':   parsed[4],
                'REQUEST_METHOD': 'POST',
                'wsgi.input':     FakePayload(post_data),
            }
            r.update(extra)
            return self.request(**r)

        def head(self, path, data={}, **extra):
            "Construct a HEAD request."

            parsed = urlparse(path)
            r = {
                'CONTENT_TYPE':    'text/html; charset=utf-8',
                'PATH_INFO':       self._get_path(parsed),
                'QUERY_STRING':    urlencode(data, doseq=True) or parsed[4],
                'REQUEST_METHOD': 'HEAD',
            }
            r.update(extra)
            return self.request(**r)

        def options(self, path, data={}, **extra):
            "Constrict an OPTIONS request"

            parsed = urlparse(path)
            r = {
                'PATH_INFO':       self._get_path(parsed),
                'QUERY_STRING':    urlencode(data, doseq=True) or parsed[4],
                'REQUEST_METHOD': 'OPTIONS',
            }
            r.update(extra)
            return self.request(**r)

        def put(self, path, data={}, content_type=MULTIPART_CONTENT,
                **extra):
            "Construct a PUT request."

            put_data = self._encode_data(data, content_type)

            parsed = urlparse(path)
            r = {
                'CONTENT_LENGTH': len(put_data),
                'CONTENT_TYPE':   content_type,
                'PATH_INFO':      self._get_path(parsed),
                'QUERY_STRING':   parsed[4],
                'REQUEST_METHOD': 'PUT',
                'wsgi.input':     FakePayload(put_data),
            }
            r.update(extra)
            return self.request(**r)

        def delete(self, path, data={}, **extra):
            "Construct a DELETE request."

            parsed = urlparse(path)
            r = {
                'PATH_INFO':       self._get_path(parsed),
                'QUERY_STRING':    urlencode(data, doseq=True) or parsed[4],
                'REQUEST_METHOD': 'DELETE',
            }
            r.update(extra)
            return self.request(**r)
