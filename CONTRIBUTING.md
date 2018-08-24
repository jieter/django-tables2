# Contributing to django-tables2

You are welcome to contribute to the development of `django-tables2` in various ways:

- Discover and [report bugs](https://github.com/jieter/django-tables2/issues/new).
  Make sure to include a minimal example to show your problem.
- Propose features, add tests or fix bugs by [opening a Pull Request](https://github.com/jieter/django-tables2/compare)
- Fix documentation or translations

When contributing features or making bug fixes, please add unit tests to verify the expected behaviour.
This helps

## Coding style

We use [black](https://black.readthedocs.io/en/stable/) to format the sources, with a 100 char line length.

Before committing, run `black .`, or use `pre-commit`:

```
pip install pre-commit
pre-commit install
```

## Running the tests

With `tox` installed, you can run the test suite in all supported environments by typing `tox`.
During development, you might not want to wait for the tests to run in all environments,
in that case, use the `-e` argument to specify a specific environment.
For example `tox -e py36-2.0` will run the tests in python 3.6 with Django 2.0.
You can also run the tests only in your current environment, using
`PYTHONPATH=. ./manage.py test` (which is even quicker).

## Code coverage

To generate a html coverage report:
```
coverage run --source=django_tables2 manage.py test
coverage html
```

## Building the documentation

If you want to build the docs from within a virtualenv, and Sphinx is installed globally, use:

```
cd docs/
make html SPHINXBUILD="python $(which sphinx-build)"
```

Publishing a release
--------------------

1. Bump the version in `django-tables2/__init__.py`.
2. Update `CHANGELOG.md`.
3. Create a tag `./maintenance.py tag`.
4. Run `./maintenance.py publish`
