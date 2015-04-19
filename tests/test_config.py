# coding: utf-8
from django_tables2 import RequestConfig
from django_tables2.utils import build_request
from django.core.paginator import EmptyPage, PageNotAnInteger
from fudge import Fake
import pytest


NOTSET = object()  # unique value


@pytest.yield_fixture
def table():
    yield (Fake("Table")
           .has_attr(prefixed_page_field="page",
                     prefixed_per_page_field="per_page",
                     prefixed_order_by_field="sort"))


def test_no_querystring(table):
    request = build_request("/")
    table = table.has_attr(order_by=NOTSET).expects("paginate")
    RequestConfig(request).configure(table)
    assert table.order_by is NOTSET


def test_full_querystring(table):
    request = build_request("/?page=1&per_page=5&sort=abc")
    table = (table
             .expects("paginate").with_args(page=1, per_page=5)
             .expects("order_by").with_args("abc"))
    RequestConfig(request).configure(table)


def test_partial_querystring(table):
    request = build_request("/?page=1&sort=abc")
    table = (table
             .expects("paginate").with_args(page=1, per_page=5)
             .expects("order_by").with_args("abc"))
    RequestConfig(request, paginate={"per_page": 5}).configure(table)


def test_silent_page_not_an_integer_error(table):
    request = build_request("/")
    paginator = (Fake("Paginator")
                 .expects("page").with_args(1))
    table = (table
             .has_attr(paginator=paginator)
             .expects("paginate").with_args(page="abc")
             .raises(PageNotAnInteger))

    RequestConfig(request, paginate={"page": "abc",
                                     "silent": True}).configure(table)


def test_silent_empty_page_error(table):
    request = build_request("/")
    paginator = (Fake("Paginator")
                 .has_attr(num_pages=987)
                 .expects("page").with_args(987))
    table = (table
             .has_attr(paginator=paginator)
             .expects("paginate").with_args(page=123)
             .raises(EmptyPage))

    RequestConfig(request, paginate={"page": 123,
                                     "silent": True}).configure(table)
