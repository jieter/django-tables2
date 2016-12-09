# coding: utf-8
from __future__ import absolute_import, unicode_literals

from django.utils.html import format_html

from django_tables2.utils import Accessor, AttributeDict

from .base import Column, library

try:
    from django.urls import reverse
except ImportError:
    # to keep backward (Django <= 1.9) compatibility
    from django.core.urlresolvers import reverse


class BaseLinkColumn(Column):
    '''
    The base for other columns that render links.

    Arguments:
        text (str or callable): If set, this value will be used to render the
            text inside link instead of value. The callable gets the record
            being rendered as argument.
        attrs (dict): In addition to *attrs* keys supported by `~.Column`, the
            following are available:

             - *a* -- ``<a>`` in ``<td>`` elements.
    '''
    def __init__(self, attrs=None, text=None, *args, **kwargs):
        kwargs['attrs'] = attrs
        self.text = text
        super(BaseLinkColumn, self).__init__(*args, **kwargs)

    def text_value(self, record, value):
        if self.text is None:
            return value
        return self.text(record) if callable(self.text) else self.text

    def render_link(self, uri, record, value, attrs=None):
        '''
        Render a hyperlink.

        Arguments:
            uri (str): URI for the hyperlink
            record: record currently being rendered
            value (str): value to be wrapped in ``<a></a>``, might be overridden
                by ``self.text``
            attrs (dict): ``<a>`` tag attributes
        '''
        attrs = AttributeDict(attrs if attrs is not None else
                              self.attrs.get('a', {}))
        attrs['href'] = uri

        return format_html(
            '<a {attrs}>{text}</a>',
            attrs=attrs.as_html(),
            text=self.text_value(record, value)
        )

    def value(self, record, value):
        '''
        Returns the content for a specific cell similarly to `.render` however
        without any html content.
        '''
        return self.text_value(record, value)


@library.register
class LinkColumn(BaseLinkColumn):
    '''
    Renders a normal value as an internal hyperlink to another page.

    It's common to have the primary value in a row hyperlinked to the page
    dedicated to that record.

    The first arguments are identical to that of
    `~django.urls.reverse` and allows an internal URL to be
    described. If this argument is `None`, then `get_absolute_url`.
    (see Django references) will be used.
    The last argument *attrs* allows custom HTML attributes to be added to the
    rendered ``<a href="...">`` tag.

    Arguments:
        viewname (str): See `~django.urls.reverse`, or use `None`
            to use the model's `get_absolute_url`
        urlconf (str): See `~django.urls.reverse`.
        args (list): See `~django.urls.reverse`. [2]_
        kwargs (dict): See `~django.urls.reverse`. [2]_
        current_app (str): See `~django.urls.reverse`.
        attrs (dict): HTML attributes that are added to the rendered
            ``<a ...>...</a>`` tag.
        text (str or callable): Either static text, or a callable. If set, this
            will be used to render the text inside link instead of value (default).
            The callable gets the record being rendered as argument.

    .. [2] In order to create a link to a URL that relies on information in the
        current row, `.Accessor` objects can be used in the *args* or *kwargs*
        arguments. The accessor will be resolved using the row's record before
        `~django.urls.reverse` is called.

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

    In order to override the text value (i.e. ``<a ... >text</a>``) consider
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

    Adding attributes to the ``<a>``-tag looks like this::

        class PeopleTable(tables.Table):
            first_name = tables.LinkColumn(attrs={
                'a': {'style': 'color: red;'}
            })

    '''
    def __init__(self, viewname=None, urlconf=None, args=None, kwargs=None,
                 current_app=None, attrs=None, **extra):
        super(LinkColumn, self).__init__(attrs, **extra)
        self.viewname = viewname
        self.urlconf = urlconf
        self.args = args
        self.kwargs = kwargs
        self.current_app = current_app

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
        return self.render_link(
            self.compose_url(record, bound_column),
            record=record,
            value=value
        )


@library.register
class RelatedLinkColumn(LinkColumn):
    '''
    Render a link to a related object using related object's ``get_absolute_url``,
    same parameters as ``~.LinkColumn``
    '''

    def compose_url(self, record, bound_column):
        accessor = self.accessor if self.accessor else Accessor(bound_column.name)

        return accessor.resolve(record).get_absolute_url()
