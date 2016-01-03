# django-tables2 - An app for creating HTML tables

[![Build status](https://travis-ci.org/bradleyayers/django-tables2.svg)](https://travis-ci.org/bradleyayers/django-tables2)

django-tables2 simplifies the task of turning sets of data into HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
`django.forms` does for HTML forms. e.g.

![An example table rendered using django-tables2](http://dl.dropbox.com/u/33499139/django-tables2/example.png)

Its features include:

- Any iterable can be a data-source, but special support for Django querysets is included.
- The builtin UI does not rely on JavaScript.
- Support for automatic table generation based on a Django model.
- Supports custom column functionality via subclassing.
- Pagination.
- Column based table sorting.
- Template tag to enable trivial rendering to HTML.
- Generic view mixin.

# Example

Creating a table for a model `Simple` is as simple as:

```python
import django_tables2 as tables

class SimpleTable(tables.Table):
    class Meta:
        model = Simple
```

This would then be used in a view:

```python
def simple_list(request):
    queryset = Simple.objects.all()
    table = SimpleTable(queryset)
    return render_to_response("simple_list.html", {"table": table},
                              context_instance=RequestContext(request))
```

And finally in the template:

```
{% load django_tables2 %}
{% render_table table %}
```

This example shows one of the simplest cases, but django-tables2 can do a lot
more! Check out the [documentation](http://django-tables2.readthedocs.org/en/latest/) for more details.


# Building the documentation

If you want to build the docs from within a virtualenv, and Sphinx is installed
globally, use:

    make html SPHINXBUILD="python $(which sphinx-build)"


# Publishing a release

1. Bump the version in `django-tables2/__init__.py`.
2. Update `CHANGELOG.md`.
3. Create a tag `git tag -a v1.0.6 -m 'tagging v1.0.6'`
4. Run `python setup.py sdist upload --sign --identity=<your gpg identity>`.
