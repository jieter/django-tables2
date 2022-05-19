from unittest.mock import MagicMock, Mock
from django.core.paginator import EmptyPage, PageNotAnInteger
from django.test import SimpleTestCase, TestCase

from django_tables2 import Column, RequestConfig, Table

from .app.models import Person
from .utils import build_request

NOTSET = object()  # unique value


def MockTable(**kwargs):
    return MagicMock(
        prefixed_page_field="page",
        prefixed_per_page_field="per_page",
        prefixed_order_by_field="sort",
        **kwargs
    )


class ConfigTest(SimpleTestCase):
    def test_no_querystring(self):
        table = MockTable(order_by=NOTSET)

        RequestConfig(build_request("/")).configure(table)

        table.paginate.assert_called()
        self.assertEqual(table.order_by, NOTSET)

    def test_full_querystring(self):
        request = build_request("/?page=1&per_page=5&sort=abc")
        table = MockTable()

        RequestConfig(request).configure(table)

        table.paginate.assert_called_with(page=1, per_page=5)
        self.assertEqual(table.order_by, ["abc"])

    def test_partial_querystring(self):
        table = MockTable()
        request = build_request("/?page=1&sort=abc")

        RequestConfig(request, paginate={"per_page": 5}).configure(table)

        table.paginate.assert_called_with(page=1, per_page=5)
        self.assertEqual(table.order_by, ["abc"])

    def test_silent_page_not_an_integer_error(self):
        request = build_request("/")
        table = MockTable(paginate=Mock(side_effect=PageNotAnInteger), paginator=MagicMock())

        RequestConfig(request, paginate={"page": "abc", "silent": True}).configure(table)

        table.paginate.assert_called_with(page="abc")
        table.paginator.page.assert_called_with(1)

    def test_silent_empty_page_error(self):
        request = build_request("/")
        table = MockTable(paginate=Mock(side_effect=EmptyPage), paginator=MagicMock(num_pages=987))

        RequestConfig(request, paginate={"page": 123, "silent": True}).configure(table)

        table.paginator.page.assert_called_with(987)

    def test_passing_request_to_constructor(self):
        """Table constructor should call RequestConfig if a request is passed."""

        request = build_request("/?page=1&sort=abc")

        class SimpleTable(Table):
            abc = Column()

        table = SimpleTable([{}], request=request)
        self.assertTrue(table.columns["abc"].is_ordered)

    def test_request_is_added_to_the_table(self):
        table = MockTable()
        request = build_request("/")

        RequestConfig(request, paginate=False).configure(table)

        self.assertEqual(table.request, request)


class NoPaginationQueriesTest(TestCase):
    def test_should_not_count_with_paginate_False(self):
        """
        No extra queries with pagination turned off.

        https://github.com/jieter/django-tables2/issues/551
        """

        class MyTable(Table):
            first_name = Column()

            class Meta:
                template_name = "minimal.html"

        request = build_request()

        Person.objects.create(first_name="Talip", last_name="Molenschot")

        table = MyTable(Person.objects.all())
        RequestConfig(request, paginate=False).configure(table)

        with self.assertNumQueries(1):
            html = table.as_html(request)

        self.assertIn("<table>", html)
