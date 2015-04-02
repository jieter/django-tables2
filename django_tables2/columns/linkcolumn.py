# coding: utf-8
from __future__ import absolute_import, unicode_literals
from django.core.urlresolvers import reverse
from django.utils.html import escape
from django.utils.safestring import mark_safe
import warnings
from .base import Column, library
from django_tables2.utils import A, AttributeDict


class BaseLinkColumn(Column):
    """
    The base for other columns that render links.

    Adds support for an ``a`` key in *attrs** which is added to the rendered
    ``<a href="...">`` tag.
    """
    def __init__(self, attrs=None, *args, **kwargs):
        valid = set(("a", "th", "td", "cell"))
        if attrs and not set(attrs) & set(valid):
            # if none of the keys in attrs are actually valid, assume it's some
            # old code that should be be interpreted as {"a": ...}
            warnings.warn('attrs keys must be one of %s, interpreting as {"a": %s}'
                          % (', '.join(valid), attrs), DeprecationWarning)
            attrs = {"a": attrs}
        kwargs['attrs'] = attrs
        super(BaseLinkColumn, self).__init__(*args, **kwargs)

    def render_link(self, uri, text, attrs=None):
        """
        Render a hyperlink.

        :param   uri: URI for the hyperlink
        :param  text: value wrapped in ``<a></a>``
        :param attrs: ``<a>`` tag attributes
        """
        attrs = AttributeDict(attrs if attrs is not None else
                              self.attrs.get('a', {}))
        attrs['href'] = uri
        html = '<a {attrs}>{text}</a>'.format(
            attrs=attrs.as_html(),
            text=escape(text)
        )
        return mark_safe(html)


@library.register
class LinkColumn(BaseLinkColumn):
    """
    Renders a normal value as an internal hyperlink to another page.

    It's common to have the primary value in a row hyperlinked to the page
    dedicated to that record.

    The first arguments are identical to that of
    `~django.core.urlresolvers.reverse` and allows an internal URL to be
    described. If this argument is None, then "get_absolute_url". (see Django references) will be used.
    The last argument *attrs* allows custom HTML attributes to
    be added to the rendered ``<a href="...">`` tag.

    :param    viewname: See `~django.core.urlresolvers.reverse`. or None to use get_absolute_url
    :param     urlconf: See `~django.core.urlresolvers.reverse`.
    :param        args: See `~django.core.urlresolvers.reverse`. **
    :param      kwargs: See `~django.core.urlresolvers.reverse`. **
    :param current_app: See `~django.core.urlresolvers.reverse`.
    :param       attrs: a `dict` of HTML attributes that are added to
                        the rendered ``<input type="checkbox" .../>`` tag

    ** In order to create a link to a URL that relies on information in the
    current row, `.Accessor` objects can be used in the *args* or
    *kwargs* arguments. The accessor will be resolved using the row's record
    before `~django.core.urlresolvers.reverse` is called.

    Example:

    .. code-block:: python

        # models.py
        class Person(models.Model):
            name = models.CharField(max_length=200)

        # urls.py
        urlpatterns = patterns('',
            url('people/(\d+)/', views.people_detail, name='people_detail')
        )

        # tables.py
        from django_tables2.utils import A  # alias for Accessor

        class PeopleTable(tables.Table):
            name = tables.LinkColumn('people_detail', args=[A('pk')])

    In addition to *attrs* keys supported by `.Column`, the following are
    available:

    - *a* -- ``<a>`` elements in ``<td>``.
    """
    def __init__(self, viewname=None, urlconf=None, args=None, kwargs=None,
                 current_app=None, attrs=None, **extra):
        super(LinkColumn, self).__init__(attrs, **extra)
        self.viewname = viewname
        self.urlconf = urlconf
        self.args = args
        self.kwargs = kwargs
        self.current_app = current_app

    def render(self, value, record, bound_column):  # pylint: disable=W0221
        if self.viewname:  # Use view if we have it
            uri = self.__get_url_by_view(record)
        else:
            try:  # Use get_absolute_url otherwise
                uri = record.get_absolute_url()
            except AttributeError:
                raise ValueError("No view name provided and record does not have get_absolute_url()")
        return self.render_link(uri, text=value)

    def __get_url_by_view(self, record):
        """
        Returns URL for certain record using view name passed to init.

        :param record: record to get url for (using view)
        :return: url
        """
        viewname = (self.viewname.resolve(record)
                    if isinstance(self.viewname, A)
                    else self.viewname)
        # The following params + if statements create optional arguments to
        # pass to Django's reverse() function.
        params = {}
        if self.urlconf:
            params['urlconf'] = (self.urlconf.resolve(record)
                                 if isinstance(self.urlconf, A)
                                 else self.urlconf)
        if self.args:
            params['args'] = [a.resolve(record) if isinstance(a, A) else a
                              for a in self.args]
        if self.kwargs:
            params['kwargs'] = {}
            for key, val in self.kwargs.items():
                # If we're dealing with an Accessor (A), resolve it, otherwise
                # use the value verbatim.
                params['kwargs'][str(key)] = (val.resolve(record)
                                              if isinstance(val, A) else val)
        if self.current_app:
            params['current_app'] = (self.current_app.resolve(record)
                                     if isinstance(self.current_app, A)
                                     else self.current_app)
        uri = reverse(viewname, **params)
        return uri
