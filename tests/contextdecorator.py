from attest import assert_hook, Tests
from contextlib import contextmanager
from django_attest import contextdecorator


stack = []


@contextdecorator
def pusher(item="a"):
    stack.append(item)
    try:
        yield
    finally:
        stack.append(item.upper())


def reset():
    stack[:] = []
    try:
        yield
    finally:
        stack[:] = []


suite = Tests()
suite.context(reset)


@suite.test
def decorator_no_args():
    @pusher
    def foo():
        pass

    assert stack == []
    foo()
    assert stack == ["a", "A"]


@suite.test
def decorator_with_args():
    @pusher(item="b")
    def foo():
        pass

    assert stack == []
    foo()
    assert stack == ["b", "B"]


@suite.test
def contextmanager_no_args():
    assert stack == []
    with contextmanager(pusher)():
        pass
    assert stack == ["a", "A"]


@suite.test
def contextmanager_with_args():
    assert stack == []
    with contextmanager(pusher(item="b"))():
        pass
    assert stack == ["b", "B"]
