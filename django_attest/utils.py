from contextlib import contextmanager
from functools import wraps


__all__ = ("contextdecorator", )


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
