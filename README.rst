================================================
django-tables2 - An app for creating HTML tables
================================================

.. note::

    Prior to v0.6.0 this package was a fork of miracle2k's and both were known
    as *django-tables*. This caused some problems (e.g. ambiguity and inability
    to put this library on PyPI) so as of v0.6.0 this package is known as
    *django-tables2*.

django-tables2 simplifies the task of turning sets of data into HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
``django.forms`` does for HTML forms. e.g.

.. figure:: http://dl.dropbox.com/u/33499139/django-tables2/example.png
    :align: center
    :alt: An example table rendered using django-tables2


Its features include:

- Any iterable can be a data-source, but special support for Django querysets
  is included.
- The builtin UI does not rely on JavaScript.
- Support for automatic table generation based on a Django model.
- Supports custom column functionality via subclassing.
- Pagination.
- Column based table sorting.
- Template tag to enable trivial rendering to HTML.
- Generic view mixin for use in Django 1.3.

Creating a table is as simple as::

    import django_tables2 as tables

    class SimpleTable(tables.Table):
        class Meta:
            model = Simple

This would then be used in a view::

    def simple_list(request):
        queryset = Simple.objects.all()
        table = SimpleTable(queryset)
        return render_to_response("simple_list.html", {"table": table},
                                  context_instance=RequestContext(request))

And finally in the template::

    {% load django_tables2 %}
    {% render_table table %}


This example shows one of the simplest cases, but django-tables2 can do a lot
more! Check out the `documentation`__ for more details.

.. __: http://django-tables2.readthedocs.org/en/latest/


Building the documentation
==========================

If you want to build the docs from within a virtualenv, use::

    make html SPHINXBUILD="python $(which sphinx-build)"


Change log
==========

v0.7.8
------

- Tables now support using both ``sequence`` and ``exclude`` (issue #32).
- ``Sequence`` class moved to ``django_tables2/utils.py``.
- Table instances now support modification to the ``exclude`` property.
- Removed ``BoundColumns._spawn_columns``.
- ``Table.data``, ``Table.rows``, and ``Table.columns`` are now attributes
  rather than properties.
