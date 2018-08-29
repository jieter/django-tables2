from __future__ import absolute_import, unicode_literals

from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.test import TestCase

from django_tables2 import LazyPaginator


class FakeQuerySet:
    objects = range(1, 10 ** 6)

    def count(self):
        raise AssertionError("LazyPaginator should not call QuerySet.count()")

    def __getitem__(self, key):
        return self.objects[key]

    def __iter__(self):
        yield next(self.objects)


class LazyPaginatorTest(TestCase):
    def test_compare_to_default_paginator(self):
        objects = list(range(1, 1000))

        paginator = Paginator(objects, 10)
        lazy_paginator = LazyPaginator(objects, 10)
        self.assertEqual(paginator.page(1).object_list, lazy_paginator.page(1).object_list)
        self.assertEqual(paginator.page(10).object_list, lazy_paginator.page(10).object_list)
        self.assertEqual(paginator.page(100).object_list, lazy_paginator.page(100).object_list)

    def test_no_count_call(self):
        paginator = LazyPaginator(FakeQuerySet(), 10)
        # num_pages initially is None, but is page_number + 1 after requesting a page.
        self.assertEqual(paginator.num_pages, None)

        paginator.page(1)
        self.assertEqual(paginator.num_pages, 2)
        paginator.page(3)
        self.assertEqual(paginator.num_pages, 4)

        paginator.page(1.0)
        # and again decreases when a lower page nu
        self.assertEqual(paginator.num_pages, 2)

        with self.assertRaises(PageNotAnInteger):
            paginator.page(1.5)

        with self.assertRaises(EmptyPage):
            paginator.page(-1)

        with self.assertRaises(NotImplementedError):
            paginator.count()

        with self.assertRaises(NotImplementedError):
            paginator.page_range()

        # last page
        last_page_number = 10 ** 5
        paginator.page(last_page_number)

        with self.assertRaises(EmptyPage):
            paginator.page(last_page_number + 1)

    def test_lookahead(self):
        objects = list(range(1, 1000))
        paginator = LazyPaginator(objects, 10, look_ahead=3)

        self.assertEqual(paginator.look_ahead, 3)
        self.assertEqual(paginator.page(1).object_list, list(range(1, 11)))
        self.assertEqual(paginator.num_pages, 4)

        self.assertEqual(paginator.page(98).object_list, list(range(971, 981)))
        self.assertEqual(paginator.num_pages, 100)
