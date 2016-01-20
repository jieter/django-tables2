# coding: utf-8
from __future__ import absolute_import, unicode_literals

import warnings

from django.core.urlresolvers import reverse
from django.utils.html import format_html

from django_tables2.utils import Accessor, AttributeDict

from .base import Column, library


class BaseLinkColumn(Column):
    """
    The base for other columns that render links.

    Adds support for an ``a`` key in *attrs** which is added to the rendered
    ``<a href="...">`` tag.
    """
    def __init__(self, attrs=None, *args, **kwargs):
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

        return format_html('<a {attrs}>{text}</a>',
                           attrs=attrs.as_html(),
                           text=text)


@library.register
class LinkColumn(BaseLinkColumn):
    """
    Renders a normal value as an internal hyperlink to another page.

    It's common to have the primary value in a row hyperlinked to the page
    dedicated to that record.

    The first arguments are identical to that of
    `~django.core.urlresolvers.reverse` and allows an internal URL to be
    described. If this argument is `None`, then `get_absolute_url`.
    (see Django references) will be used.
    The last argument *attrs* allows custom HTML attributes to be added to the
    rendered ``<a href="...">`` tag.

    :param    viewname: See `~django.core.urlresolvers.reverse`.
                        Or use `None` to use Model's `get_absolute_url`
    :param     urlconf: See `~django.core.urlresolvers.reverse`.
    :param        args: See `~django.core.urlresolvers.reverse`. **
    :param      kwargs: See `~django.core.urlresolvers.reverse`. **
    :param current_app: See `~django.core.urlresolvers.reverse`.
    :param       attrs: a `dict` of HTML attributes that are added to
                        the rendered ``<input type="checkbox" .../>`` tag
    :param        text: Either static text, or a callable. If set, this
                        value will be used to render the text inside link
                        instead of value (default)

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

    In order to override the text value (i.e. <a ... >text</a>) consider
    the following example:

    .. code-block:: python

        # tables.py
        from django_tables2.utils import A  # alias for Accessor

        class PeopleTable(tables.Table):
            name = tables.LinkColumn('people_detail', text='static text', args=[A('pk')])
            age  = tables.LinkColumn('people_detail', text=lambda record: record.name, args=[A('pk')])

    In the first example, a static text would be rendered ('static text')
    In the second example, you can specify a callable which accepts a record object (and thus
    can return anything from it)

    In addition to *attrs* keys supported by `.Column`, the following are
    available:

    - *a* -- ``<a>`` elements in ``<td>``.
    """
    def __init__(self, viewname=None, urlconf=None, args=None, kwargs=None,
                 current_app=None, attrs=None, text=None, **extra):
        super(LinkColumn, self).__init__(attrs, **extra)
        self.viewname = viewname
        self.urlconf = urlconf
        self.args = args
        self.kwargs = kwargs
        self.current_app = current_app
        self.text_value = text

    def compose_url(self, record, *args, **kwargs):
        '''Compose the url if the column is constructed with a viewname.'''

        if self.viewname is None:
            if not hasattr(record, 'get_absolute_url'):
                raise TypeError('if viewname=None, record must define a get_absolute_url')
            return record.get_absolute_url()

        def resolve_if_accessor(val):
            return val.resolve(record) if isinstance(val, Accessor) else val

        viewname = resolve_if_accessor(self.viewname)

        # Collect the optional arguments for django's reverse()
        params = {}
        if self.urlconf:
            params['urlconf'] = resolve_if_accessor(self.urlconf)
        if self.args:
            params['args'] = [resolve_if_accessor(a) for a in self.args]
        if self.kwargs:
            params['kwargs'] = {key: resolve_if_accessor(val) for key, val in self.kwargs.items()}
        if self.current_app:
            params['current_app'] = resolve_if_accessor(self.current_app)

        return reverse(viewname, **params)

    def render(self, value, record, bound_column):
        text_value = value
        if self.text_value:
            text_value = self.text_value
            if callable(text_value):
                text_value = text_value(record)

        return self.render_link(self.compose_url(record, bound_column), text=text_value)


@library.register
class RelatedLinkColumn(LinkColumn):
    '''render a link to a related object using get_absolute_url for the related object'''

    def compose_url(self, record, bound_column):
        accessor = self.accessor if self.accessor else Accessor(bound_column)

        return accessor.resolve(record).get_absolute_url()
