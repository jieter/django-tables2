.. _accessors:

Specifying alternative data for a column
========================================

Each column has a "key" that describes which value to pull from each record to
populate the column's cells. By default, this key is just the name given to the
column, but it can be changed to allow foreign key traversal or other complex
cases.

To reduce ambiguity, rather than calling it a "key", it's been given the
special name "accessor".

Accessors are just dotted paths that describe how an object should be traversed
to reach a specific value. To demonstrate how they work we'll use them
directly::

    >>> from django_tables2 import A
    >>> data = {'abc': {'one': {'two': 'three'}}}
    >>> A('abc.one.two').resolve(data)
    'three'

Dots represent a relationships, and are attempted in this order:

1. Dictionary lookup ``a[b]``
2. Attribute lookup ``a.b``
3. List index lookup ``a[int(b)]``

Then, if the value is callable, it is called and the result is used.
