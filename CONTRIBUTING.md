# Contributing to django-tables2

You are welcome to contribute to the development of `django-tables2` in various ways:

- Discover and [report bugs](https://github.com/bradleyayers/django-tables2/issues/new).
  Make sure to include a minimal example to show your problem.
- Propose features or fix bugs by [opening a Pull Request](https://github.com/bradleyayers/django-tables2/compare)
- Fix documenation or translations

When contributing code or making bug fixes, we need to have unit tests to verify the expected behaviour.

## Running the tests

With `tox` installed, you can run the test suite by typing `tox`.
It will take care of installing the correct dependencies. During development,
you might not want to wait for the tests to run in all environments.
In that case, use the `-e` argument to specify an environment:
`tox -e py27-1.9` to run the tests in python 2.7 with Django 1.9,
or `PYTHONPATH=. py.test` to run the tests against your current environment (which is even quicker).

## Code coverage

To generate a html coverage report:
```
PYTHONPATH=. py.test -s --cov=django_tables2 --cov-report html
```

## Building the documentation

If you want to build the docs from within a virtualenv, and Sphinx is installed
globally, use:

```
cd docs/
make html SPHINXBUILD="python $(which sphinx-build)"
```

Publishing a release
--------------------

1. Bump the version in `django-tables2/__init__.py`.
2. Update CHANGELOG.md`.
3. Create a tag `./setup.py tag` or `git tag -a v1.0.6 -m 'tagging v1.0.6'`
4. Run `./setup.py publish` or `python setup.py sdist upload --sign --identity=<your gpg identity>`.
