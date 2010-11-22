-----------
MemoryTable
-----------

This table expects an iterable of ``dict`` (or compatible) objects as the
data source. Values found in the data that are not associated with a column
are ignored, missing values are replaced by the column default or ``None``.

Sorting is done in memory, in pure Python.

Dynamic Data
~~~~~~~~~~~~

If any value in the source data is a callable, it will be passed it's own
row instance and is expected to return the actual value for this particular
table cell.

Similarily, the colunn default value may also be callable that will take
the row instance as an argument (representing the row that the default is
needed for).
