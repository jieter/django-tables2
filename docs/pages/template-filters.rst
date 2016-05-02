Template filters
================

title
-----

String filter that performs title case conversion on a per-word basis, leaving
words containing upper-case letters alone.

.. sourcecode:: django

    {{ "start 6PM"|title }}   # Start 6PM
    {{ "sTart 6pm"|title }}   # sTart 6pm

.. warning::

    Be careful when loading the ``django_tables2`` template library to not
    inadvertently load ``title``. You should always use the
    ``{% load ... from ... %}`` syntax.
