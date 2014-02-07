# coding: utf-8
from attest import assert_hook, raises, Tests
from django_tables2.utils import (Accessor, AttributeDict, computed_values,
                                  OrderByTuple, OrderBy, segment)
import itertools
import six


utils = Tests()


@utils.test
def orderbytuple():
    obt = OrderByTuple(('a', 'b', 'c'))
    assert obt == (OrderBy('a'), OrderBy('b'), OrderBy('c'))

    # indexing
    assert obt[0] == OrderBy('a')
    assert obt['b'] == OrderBy('b')
    with raises(KeyError):
        obt['d']
    with raises(TypeError):
        obt[('tuple', )]

    # .get
    sentinel = object()
    assert obt.get('b', sentinel) is obt['b']  # keying
    assert obt.get('-', sentinel) is sentinel
    assert obt.get(0,   sentinel) is obt['a']  # indexing
    assert obt.get(3,   sentinel) is sentinel

    # .opposite
    assert OrderByTuple(('a', '-b', 'c')).opposite == ('-a', 'b', '-c')

    # in
    assert 'a' in obt and '-a' in obt


@utils.test
def orderbytuple_sort_key_multiple():
    obt = OrderByTuple(('a', '-b'))
    items = [
        {"a": 1, "b": 2},
        {"a": 1, "b": 3},
    ]
    assert sorted(items, key=obt.key) == [
        {"a": 1, "b": 3},
        {"a": 1, "b": 2},
    ]


@utils.test
def orderbytuple_sort_key_empty_comes_first():
    obt = OrderByTuple(('a'))
    items = [
        {"a": 1},
        {"a": ""},
        {"a": 2},
    ]
    if six.PY3:
        assert sorted(items, key=obt.key) == [
            {"a": ""},
            {"a": 1},
            {"a": 2},
        ]
    else:
        assert sorted(items, key=obt.key) == [
            {"a": 1},
            {"a": 2},
            {"a": ""},
        ]

@utils.test
def orderby():
    a = OrderBy('a')
    assert 'a' == a
    assert 'a' == a.bare
    assert '-a' == a.opposite
    assert True == a.is_ascending
    assert False == a.is_descending

    b = OrderBy('-b')
    assert '-b' == b
    assert 'b' == b.bare
    assert 'b' == b.opposite
    assert True == b.is_descending
    assert False == b.is_ascending


@utils.test
def accessor():
    x = Accessor('0')
    assert 'B' == x.resolve('Brad')

    x = Accessor('1')
    assert 'r' == x.resolve('Brad')

    x = Accessor('2.upper')
    assert 'A' == x.resolve('Brad')

    x = Accessor('2.upper.__len__')
    assert 1 == x.resolve('Brad')

    x = Accessor('')
    assert 'Brad' == x.resolve('Brad')


@utils.test
def accessor_wont_honors_alters_data():
    class Foo(object):
        deleted = False

        def delete(self):
            self.deleted = True
        delete.alters_data = True

    foo = Foo()
    with raises(ValueError):
        Accessor('delete').resolve(foo)
    assert foo.deleted is False


@utils.test
def accessor_can_be_quiet():
    foo = {}
    assert Accessor("bar").resolve(foo, quiet=True) is None


@utils.test
def attribute_dict_handles_escaping():
    x = AttributeDict({"x": '"\'x&'})
    assert x.as_html() == 'x="&quot;&#39;x&amp;"'


@utils.test
def compute_values_supports_shallow_structures():
    x = computed_values({"foo": lambda: "bar"})
    assert x == {"foo": "bar"}


@utils.test
def compute_values_supports_shallow_structures():
    x = computed_values({"foo": lambda: {"bar": lambda: "baz"}})
    assert x == {"foo": {"bar": "baz"}}


@utils.test
def segment_should_return_all_candidates():
    assert set(segment(("a", "-b", "c"), {
        "x": ("a"),
        "y": ("b", "-c"),
        "-z": ("b", "-c"),
    })) == set((
        ("x", "-y"),
        ("x", "z"),
    ))
