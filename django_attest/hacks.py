# coding: utf-8
from contextlib import contextmanager
from functools  import wraps
import types


@contextmanager
def django12_debug_cursor(conn):
    """
    Monkey patch Django 1.2 to make its database debug cursor behave like
    Django 1.3 and later.

    In Django 1.2, debug cursors are enabled *only* when ``DEBUG = True``. In
    later versions they can also be enabled via
    ``BaseDatabaseWrapper.use_debug_cursor = True``. This is a good approach
    because it avoids possible side effects caused by ``DEBUG = True``.
    """
    original = conn.cursor

    @wraps(original)
    def patched(self):
        from django.conf import settings
        cursor = self._cursor()
        if (self.use_debug_cursor or
            (self.use_debug_cursor is None and settings.DEBUG)):
            return self.make_debug_cursor(cursor)
        return cursor

    try:
        conn.use_debug_cursor = None
        conn.cursor = types.MethodType(patched, conn)
        yield
    finally:
        conn.cursor = original
        del conn.use_debug_cursor
