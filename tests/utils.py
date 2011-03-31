# -*- coding: utf8 -*-
from django_tables.utils import OrderByTuple, OrderBy
from attest import Tests, Assert


utils = Tests()


@utils.test
def orderbytuple():
    obt = OrderByTuple('abc')
    Assert(obt) == (OrderBy('a'), OrderBy('b'), OrderBy('c'))
    Assert(obt[0]) == OrderBy('a')
    Assert(obt['b']) == OrderBy('b')
    with Assert.raises(IndexError) as error:
        obt['d']
    with Assert.raises(TypeError) as error:
        obt[('tuple', )]


@utils.test
def orderby():
    a = OrderBy('a')
    Assert('a') == a
    Assert('a') == a.bare
    Assert('-a') == a.opposite
    Assert(True) == a.is_ascending
    Assert(False) == a.is_descending

    b = OrderBy('-b')
    Assert('-b') == b
    Assert('b') == b.bare
    Assert('b') == b.opposite
    Assert(True) == b.is_descending
    Assert(False) == b.is_ascending
