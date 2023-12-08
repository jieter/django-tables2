from django.db import models
from django.test import TestCase

from django_tables2.utils import (
    Accessor,
    AttributeDict,
    OrderBy,
    OrderByTuple,
    Sequence,
    call_with_appropriate,
    computed_values,
    segment,
    signature,
)


class OrderByTupleTest(TestCase):
    def test_basic(self):
        obt = OrderByTuple(("a", "b", "c"))
        assert obt == (OrderBy("a"), OrderBy("b"), OrderBy("c"))

    def test_indexing(self):
        obt = OrderByTuple(("a", "b", "c"))
        assert obt[0] == OrderBy("a")
        assert obt["b"] == OrderBy("b")
        with self.assertRaises(KeyError):
            obt["d"]
        with self.assertRaises(TypeError):
            obt[("tuple",)]

    def test_get(self):
        obt = OrderByTuple(("a", "b", "c"))
        sentinel = object()
        assert obt.get("b", sentinel) is obt["b"]  # keying
        assert obt.get("-", sentinel) is sentinel
        assert obt.get(0, sentinel) is obt["a"]  # indexing
        assert obt.get(3, sentinel) is sentinel

    def test_opposite(self):
        assert OrderByTuple(("a", "-b", "c")).opposite == ("-a", "b", "-c")

    def test_in(self):
        obt = OrderByTuple(("a", "b", "c"))
        assert "a" in obt and "-a" in obt

    def test_sort_key_multiple(self):
        obt = OrderByTuple(("a", "-b"))
        items = [{"a": 1, "b": 2}, {"a": 1, "b": 3}]
        assert sorted(items, key=obt.key) == [{"a": 1, "b": 3}, {"a": 1, "b": 2}]

    def test_sort_key_empty_comes_first(self):
        obt = OrderByTuple("a")
        items = [{"a": 1}, {"a": ""}, {"a": 2}]
        assert sorted(items, key=obt.key) == [{"a": ""}, {"a": 1}, {"a": 2}]


class OrderByTest(TestCase):
    def test_orderby_ascending(self):
        a = OrderBy("a")
        self.assertEqual(a, "a")
        self.assertEqual(a.bare, "a")
        self.assertEqual(a.opposite, "-a")
        self.assertTrue(a.is_ascending)
        self.assertFalse(a.is_descending)

    def test_orderby_descending(self):
        b = OrderBy("-b")
        self.assertEqual(b, "-b")
        self.assertEqual(b.bare, "b")
        self.assertEqual(b.opposite, "b")
        self.assertTrue(b.is_descending)
        self.assertFalse(b.is_ascending)

    def test_error_on_legacy_separator(self):
        message = "Use '__' to separate path components, not '.' in accessor 'a.b'"
        with self.assertWarnsRegex(DeprecationWarning, message):
            OrderBy("a.b")

    def test_for_queryset(self):
        ab = OrderBy("a.b")
        self.assertEqual(ab.for_queryset(), "a__b")
        ab = OrderBy("a__b")
        self.assertEqual(ab.for_queryset(), "a__b")


class AccessorTest(TestCase):
    def test_bare(self):
        self.assertEqual(Accessor("").resolve("Brad"), "Brad")
        self.assertEqual(Accessor("").resolve({"Brad"}), {"Brad"})
        self.assertEqual(Accessor("").resolve({"Brad": "author"}), {"Brad": "author"})

    def test_index_lookup(self):
        self.assertEqual(Accessor("0").resolve("Brad"), "B")
        self.assertEqual(Accessor("1").resolve("Brad"), "r")
        self.assertEqual(Accessor("-1").resolve("Brad"), "d")
        self.assertEqual(Accessor("-2").resolve("Brad"), "a")

    def test_calling_methods(self):
        self.assertEqual(Accessor("2__upper").resolve("Brad"), "A")

    def test_error_on_legacy_separator(self):
        message = "Use '__' to separate path components, not '.' in accessor '2.upper'"
        with self.assertWarnsRegex(DeprecationWarning, message):
            Accessor("2.upper")

    def test_honors_alters_data(self):
        class Foo:
            deleted = False

            def delete(self):
                self.deleted = True

            delete.alters_data = True

        foo = Foo()
        with self.assertRaisesMessage(ValueError, "Refusing to call delete() because"):
            Accessor("delete").resolve(foo)
        self.assertFalse(foo.deleted)

    def test_accessor_can_be_quiet(self):
        self.assertIsNone(Accessor("bar").resolve({}, quiet=True))

    def test_penultimate(self):
        context = {"a": {"a": 1, "b": {"c": 2, "d": 4}}}
        self.assertEqual(Accessor("a__b__c").penultimate(context), (context["a"]["b"], "c"))
        self.assertEqual(Accessor("a___b___c___d___e").penultimate(context), (None, "e"))

    def test_short_circuit_dict(self):
        context = {"occupation__name": "Carpenter"}

        self.assertEqual(Accessor("occupation__name").resolve(context), "Carpenter")

    def test_callable_args_kwargs(self):
        class MyClass:
            def method(self, *args, **kwargs):
                return args, kwargs

        callable_args = ("arg1", "arg2")
        callable_kwargs = {"kwarg1": "val1", "kwarg2": "val2"}
        obj = MyClass()
        result = Accessor("method", *callable_args, **callable_kwargs).resolve(obj)
        self.assertEqual(result, (callable_args, callable_kwargs))


class AccessorTestModel(models.Model):
    foo = models.CharField(max_length=20)

    class Meta:
        app_label = "tests"


class AccessorModelTests(TestCase):
    def test_can_return_field(self):
        context = AccessorTestModel(foo="bar")
        self.assertIsInstance(Accessor("foo").get_field(context), models.CharField)

    def test_returns_None_when_doesnt_exist(self):
        context = AccessorTestModel(foo="bar")
        self.assertIsNone(Accessor("bar").get_field(context))

    def test_returns_None_if_not_a_model(self):
        context = {"bar": 234}
        self.assertIsNone(Accessor("bar").get_field(context))


class AttributeDictTest(TestCase):
    def test_handles_escaping(self):
        # django==3.0 replaces &#39; with &#x27;, drop first option if django==2.2 support is removed
        self.assertIn(
            AttributeDict({"x": "\"'x&"}).as_html(),
            ('x="&quot;&#39;x&amp;"', 'x="&quot;&#x27;x&amp;"'),
        )

    def test_omits_None(self):
        self.assertEqual(AttributeDict({"x": None}).as_html(), "")

    def test_self_wrap(self):
        x = AttributeDict({"x": "y"})

        self.assertEqual(x, AttributeDict(x))


class ComputedValuesTest(TestCase):
    def test_supports_shallow_structures(self):
        x = computed_values({"foo": lambda: "bar"})
        self.assertEqual(x, {"foo": "bar"})

    def test_supports_nested_structures(self):
        x = computed_values({"foo": lambda: {"bar": lambda: "baz"}})
        self.assertEqual(x, {"foo": {"bar": "baz"}})

    def test_with_argument(self):
        x = computed_values({"foo": lambda y: {"bar": lambda y: f"baz-{y}"}}, kwargs=dict(y=2))
        self.assertEqual(x, {"foo": {"bar": "baz-2"}})

    def test_returns_None_if_not_enough_kwargs(self):
        x = computed_values({"foo": lambda x: "bar"})
        self.assertEqual(x, {"foo": None})


class SegmentTest(TestCase):
    def test_should_return_all_candidates(self):
        assert set(segment(("a", "-b", "c"), {"x": "a", "y": ("b", "-c"), "-z": ("b", "-c")})) == {
            ("x", "-y"),
            ("x", "z"),
        }


class SequenceTest(TestCase):
    def test_multiple_ellipsis(self):
        sequence = Sequence(["foo", "...", "bar", "..."])

        with self.assertRaisesMessage(ValueError, "'...' must be used at most once in a sequence."):
            sequence.expand(["foo"])


class SignatureTest(TestCase):
    def test_basic(self):
        def foo(bar, baz):
            pass

        args, keywords = signature(foo)
        assert args == ("bar", "baz")
        assert keywords is None

    def test_signature_method(self):
        class Foo:
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
        assert args == ("bar", "baz")
        assert keywords is None

        args, keywords = signature(obj.baz)
        assert args == ("bar",)
        assert keywords == "boo"

    def test_catch_all_kwargs(self):
        def foo(bar, baz, **kwargs):
            pass

        args, keywords = signature(foo)
        assert args == ("bar", "baz")
        assert keywords == "kwargs"


class CallWithAppropriateTest(TestCase):
    def test_basic(self):
        def foo():
            return "bar"

        assert call_with_appropriate(foo, {"a": "d", "c": "e"}) == "bar"

        def bar(baz):
            return baz

        assert call_with_appropriate(bar, dict(baz=23)) == 23
