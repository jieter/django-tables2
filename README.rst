===============================================
django-tables - An app for creating HTML tables
===============================================

django-tables simplifies the task of turning sets of datainto HTML tables. It
has native support for pagination and sorting. It does for HTML tables what
``django.forms`` does for HTML forms.

Documentation_ is available on http://readthedocs.org

.. _Documentation: http://readthedocs.org/docs/django-tables/en/latest/


Building the documentation
==========================

If you want to build the docs from within a virtualenv, use::

    make html SPHINXBUILD="python $(which sphinx-build)"
