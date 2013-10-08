# coding: utf-8
from __future__ import unicode_literals
from django.core.paginator import EmptyPage, PageNotAnInteger


class RequestConfig(object):
    """
    A configurator that uses request data to setup a table.

    :type  paginate: `dict` or `bool`
    :param paginate: indicates whether to paginate, and if so, what default
                     values to use. If the value evaluates to `False`,
                     pagination will be disabled. A `dict` can be used to
                     specify default values for the call to
                     `~.tables.Table.paginate` (e.g. to define a default
                     *per_page* value).

                     A special *silent* item can be used to enable automatic
                     handling of pagination exceptions using the following
                     algorithm:

                     - If `~django.core.paginator.PageNotAnInteger`` is raised,
                       show the first page.
                     - If `~django.core.paginator.EmptyPage` is raised, show
                       the last page.

    """
    def __init__(self, request, paginate=True):
        self.request = request
        self.paginate = paginate

    def configure(self, table):
        """
        Configure a table using information from the request.
        """
        order_by = self.request.GET.getlist(table.prefixed_order_by_field)
        if order_by:
            table.order_by = order_by
        if self.paginate:
            if hasattr(self.paginate, "items"):
                kwargs = dict(self.paginate)
            else:
                kwargs = {}
            # extract some options from the request
            for arg in ("page", "per_page"):
                name = getattr(table, "prefixed_%s_field" % arg)
                try:
                    kwargs[arg] = int(self.request.GET[name])
                except (ValueError, KeyError):
                    pass

            silent = kwargs.pop('silent', True)
            if not silent:
                table.paginate(**kwargs)
            else:
                try:
                    table.paginate(**kwargs)
                except PageNotAnInteger:
                    table.page = table.paginator.page(1)
                except EmptyPage:
                    table.page = table.paginator.page(table.paginator.num_pages)

        # Call the table's configure_request method for any additional setup
        table.configure_request(self.request)