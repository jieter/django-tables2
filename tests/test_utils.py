# coding: utf-8
from unittest import TestCase

from django.db import models
from django.utils import six

from django_tables2.utils import (Accessor, AttributeDict, OrderBy, OrderByTuple, Sequence, call_with_appropriate,
                                  computed_values, segment, signature)


class OrderByTupleTest(TestCase):
    def test_basic(self):
        obt = OrderByTuple(('a', 'b', 'c'))
        assert obt == (OrderBy('a'), OrderBy('b'), OrderBy('c'))

    def test_intexing(self):
        obt = OrderByTuple(('a', 'b', 'c'))
        assert obt[0] == OrderBy('a')
        assert obt['b'] == OrderBy('b')
        with self.assertRaises(KeyError):
            obt['d']
        with self.assertRaises(TypeError):
            obt[('tuple', )]

    def test_get(self):
        obt = OrderByTuple(('a', 'b', 'c'))
        sentinel = object()
        assert obt.get('b', sentinel) is obt['b']  # keying
        assert obt.get('-', sentinel) is sentinel
        assert obt.get(0, sentinel) is obt['a']  # indexing
        assert obt.get(3, sentinel) is sentinel

    def test_opposite(self):
        assert OrderByTuple(('a', '-b', 'c')).opposite == ('-a', 'b', '-c')

    def test_in(self):
        obt = OrderByTuple(('a', 'b', 'c'))
        assert 'a' in obt and '-a' in obt

    def test_sort_key_multiple(self):
        obt = OrderByTuple(('a', '-b'))
        items = [
            {'a': 1, 'b': 2},
            {'a': 1, 'b': 3},
        ]
        assert sorted(items, key=obt.key) == [
            {'a': 1, 'b': 3},
            {'a': 1, 'b': 2},
        ]

    def test_sort_key_empty_comes_first(self):
        obt = OrderByTuple(('a'))
        items = [
            {'a': 1},
            {'a': ''},
            {'a': 2},
        ]
        if six.PY3:
            assert sorted(items, key=obt.key) == [
                {'a': ''},
                {'a': 1},
                {'a': 2},
            ]
        else:
            assert sorted(items, key=obt.key) == [
                {'a': 1},
                {'a': 2},
                {'a': ''},
            ]


class OrderByTest(TestCase):
    def test_orderby_ascending(self):
        a = OrderBy('a')
        assert 'a' == a
        assert 'a' == a.bare
        assert '-a' == a.opposite
        assert True is a.is_ascending
        assert False is a.is_descending

    def test_orderby_descending(self):
        b = OrderBy('-b')
        assert '-b' == b
        assert 'b' == b.bare
        assert 'b' == b.opposite
        assert True is b.is_descending
        assert False is b.is_ascending


class AccessorTest(TestCase):
    def test_bare(self):
        assert 'Brad' == Accessor('').resolve('Brad')
        assert {'Brad'} == Accessor('').resolve({'Brad'})
        assert {'Brad': 'author'} == Accessor('').resolve({'Brad': 'author'})

    def test_index_lookup(self):
        x = Accessor('0')
        assert 'B' == x.resolve('Brad')

        x = Accessor('1')
        assert 'r' == x.resolve('Brad')

    def test_calling_methods(self):
        x = Accessor('2.upper')
        assert 'A' == x.resolve('Brad')

        x = Accessor('2.upper.__len__')
        assert 1 == x.resolve('Brad')

    def test_honors_alters_data(self):
        class Foo(object):
            deleted = False

            def delete(self):
                self.deleted = True
            delete.alters_data = True

        foo = Foo()
        with self.assertRaises(ValueError):
            Accessor('delete').resolve(foo)
        assert foo.deleted is False

    def test_accessor_can_be_quiet(self):
        foo = {}
        assert Accessor('bar').resolve(foo, quiet=True) is None

    def test_penultimate(self):
        context = {
            'a': {
                'a': 1,
                'b': {
                    'c': 2,
                    'd': 4
                }
            }
        }
        assert Accessor('a.b.c').penultimate(context) == (context['a']['b'], 'c')
        assert Accessor('a.b.c.d.e').penultimate(context) == (None, 'e')


class AccessorTestModel(models.Model):
    foo = models.CharField(max_length=20)

    class Meta:
        app_label = 'tests'


class AccessorModelTests(TestCase):
    def test_can_return_field(self):
        context = AccessorTestModel(foo='bar')
        assert type(Accessor('foo').get_field(context)) == models.CharField

    def test_returns_None_when_doesnt_exist(self):
        context = AccessorTestModel(foo='bar')
        assert Accessor('bar').get_field(context) is None

    def test_returns_None_if_not_a_model(self):
        context = {'bar': 234}
        assert Accessor('bar').get_field(context) is None


class AttributeDictTest(TestCase):
    def test_handles_escaping(self):
        x = AttributeDict({'x': '"\'x&'})
        assert x.as_html() == 'x="&quot;&#39;x&amp;"'

    def test_omits_None(self):
        x = AttributeDict({'x': None})
        assert x.as_html() == ''


class ComputedValuesTest(TestCase):
    def test_supports_shallow_structures(self):
        x = computed_values({'foo': lambda: 'bar'})
        assert x == {'foo': 'bar'}

    def test_supports_nested_structures(self):
        x = computed_values({'foo': lambda: {'bar': lambda: 'baz'}})
        assert x == {'foo': {'bar': 'baz'}}

    def test_with_argument(self):
        x = computed_values({
            'foo': lambda y: {
                'bar': lambda y: 'baz-{}'.format(y)
            }
        }, kwargs=dict(y=2))
        assert x == {'foo': {'bar': 'baz-2'}}

    def test_returns_None_if_not_enough_kwargs(self):
        x = computed_values({'foo': lambda x: 'bar'})
        assert x == {'foo': None}


class SegmentTest(TestCase):
    def test_should_return_all_candidates(self):
        assert set(segment(('a', '-b', 'c'), {
            'x': 'a',
            'y': ('b', '-c'),
            '-z': ('b', '-c'),
        })) == {
            ('x', '-y'),
            ('x', 'z'),
        }


class SequenceTest(TestCase):
    def test_multiple_ellipsis(self):
        sequence = Sequence(['foo', '...', 'bar', '...'])

        with self.assertRaises(ValueError):
            sequence.expand(['foo'])


class SignatureTest(TestCase):
    def test_basic(self):
        def foo(bar, baz):
            pass

        args, keywords = signature(foo)
        assert args == ('bar', 'baz')
        assert keywords is None

    def test_signature_method(self):
        class Foo(object):
            def foo(self):
                pass

            def bar(self, bar, baz):
                pass

            def baz(self, bar, *bla, **boo):
                pass

        obj = Foo()
        args, keywords = signature(obj.foo)
        assert args == ()
        assert keywords is None

        args, keywords = signature(obj.bar)
        assert args == ('bar', 'baz')
        assert keywords is None

        args, keywords = signature(obj.baz)
        assert args == ('bar', )
        assert keywords == 'boo'

    def test_catch_all_kwargs(self):
        def foo(bar, baz, **kwargs):
            pass

        args, keywords = signature(foo)
        assert args == ('bar', 'baz')
        assert keywords == 'kwargs'


class CallWithAppropriateTest(TestCase):
    def test_basic(self):
        def foo():
            return 'bar'

        assert call_with_appropriate(foo, {
            'a': 'd',
            'c': 'e'
        }) == 'bar'

        def bar(baz):
            return baz

        assert call_with_appropriate(bar, dict(baz=23)) == 23
