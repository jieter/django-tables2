# coding: utf-8
# from attest import assert_hook, raises, Tests
import pytest
import six

from django_tables2.utils import (Accessor, AttributeDict, OrderBy,
                                  OrderByTuple, Sequence, computed_values,
                                  segment)


def test_orderbytuple():
    obt = OrderByTuple(('a', 'b', 'c'))
    assert obt == (OrderBy('a'), OrderBy('b'), OrderBy('c'))

    # indexing
    assert obt[0] == OrderBy('a')
    assert obt['b'] == OrderBy('b')
    with pytest.raises(KeyError):
        obt['d']
    with pytest.raises(TypeError):
        obt[('tuple', )]

    # .get
    sentinel = object()
    assert obt.get('b', sentinel) is obt['b']  # keying
    assert obt.get('-', sentinel) is sentinel
    assert obt.get(0, sentinel) is obt['a']  # indexing
    assert obt.get(3, sentinel) is sentinel

    # .opposite
    assert OrderByTuple(('a', '-b', 'c')).opposite == ('-a', 'b', '-c')

    # in
    assert 'a' in obt and '-a' in obt


def test_orderbytuple_sort_key_multiple():
    obt = OrderByTuple(('a', '-b'))
    items = [
        {"a": 1, "b": 2},
        {"a": 1, "b": 3},
    ]
    assert sorted(items, key=obt.key) == [
        {"a": 1, "b": 3},
        {"a": 1, "b": 2},
    ]


def test_orderbytuple_sort_key_empty_comes_first():
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


def test_orderby():
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


def test_accessor():
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


def test_accessor_wont_honors_alters_data():
    class Foo(object):
        deleted = False

        def delete(self):
            self.deleted = True
        delete.alters_data = True

    foo = Foo()
    with pytest.raises(ValueError):
        Accessor('delete').resolve(foo)
    assert foo.deleted is False


def test_accessor_can_be_quiet():
    foo = {}
    assert Accessor("bar").resolve(foo, quiet=True) is None


def test_attribute_dict_handles_escaping():
    x = AttributeDict({"x": '"\'x&'})
    assert x.as_html() == 'x="&quot;&#39;x&amp;"'


def test_compute_values_supports_shallow_structures():
    x = computed_values({"foo": lambda: "bar"})
    assert x == {"foo": "bar"}


def test_compute_values_supports_nested_structures():
    x = computed_values({"foo": lambda: {"bar": lambda: "baz"}})
    assert x == {"foo": {"bar": "baz"}}


def test_segment_should_return_all_candidates():
    assert set(segment(("a", "-b", "c"), {
        "x": "a",
        "y": ("b", "-c"),
        "-z": ("b", "-c"),
    })) == {
        ("x", "-y"),
        ("x", "z"),
    }


def test_sequence_multiple_ellipsis():
    sequence = Sequence(['foo', '...', 'bar', '...'])

    with pytest.raises(ValueError):
        sequence.expand(['foo'])
