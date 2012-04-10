# -*- coding: utf-8 -*-
from attest import assert_hook, Assert, Tests
from django_tables2.utils import Accessor, AttributeDict, OrderByTuple, OrderBy


utils = Tests()


@utils.test
def orderbytuple():
    obt = OrderByTuple(('a', 'b', 'c'))
    assert obt == (OrderBy('a'), OrderBy('b'), OrderBy('c'))

    # indexing
    assert obt[0] == OrderBy('a')
    assert obt['b'] == OrderBy('b')
    with Assert.raises(KeyError) as error:
        obt['d']
    with Assert.raises(TypeError) as error:
        obt[('tuple', )]

    # .get
    sentinel = object()
    assert obt.get('b', sentinel) is obt['b'] # keying
    assert obt.get('-', sentinel) is sentinel
    assert obt.get(0,   sentinel) is obt['a'] # indexing
    assert obt.get(3,   sentinel) is sentinel

    # .opposite
    assert OrderByTuple(('a', '-b', 'c')).opposite == ('-a', 'b', '-c')

    # in
    assert 'a' in obt and '-a' in obt


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
def attribute_dict_handles_escaping():
    x = AttributeDict({"x": '"\'x&'})
    assert x.as_html() == 'x="&quot;&#39;x&amp;"'
