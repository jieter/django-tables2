from attest import Tests
from django_tables2 import RequestConfig
from django.test.client import RequestFactory
from fudge import Fake


config = Tests()


@config.test
def request_config():
    factory = RequestFactory()
    request= factory.get("/?page=1&per_page=5&sort=abc")
    table = (Fake("Table")
             .has_attr(prefixed_page_field="page",
                       prefixed_per_page_field="per_page",
                       prefixed_order_by_field="sort")
             .expects("paginate").with_args(page=1, per_page=5)
             .expects("order_by").with_args("abc"))

    RequestConfig(request).configure(table)

    # Test with some defaults.
    request= factory.get("/?page=1&sort=abc")
    table = (Fake("Table")
             .has_attr(prefixed_page_field="page",
                       prefixed_per_page_field="per_page",
                       prefixed_order_by_field="sort")
             .expects("paginate").with_args(page=1, per_page=5)
             .expects("order_by").with_args("abc"))

    RequestConfig(request, paginate={"per_page": 5}).configure(table)
