__all__ = (
    'Column', 'TextColumn', 'NumberColumn',
)

class Column(object):
    """Represents a single column of a table.

    ``verbose_name`` defines a display name for this column used for output.

    ``name`` is the internal name of the column. Normally you don't need to
    specify this, as the attribute that you make the column available under
    is used. However, in certain circumstances it can be useful to override
    this default, e.g. when using ModelTables if you want a column to not
    use the model field name.

    ``default`` is the default value for this column. If the data source
    does not provide None for a row, the default will be used instead. Note
    that this currently affects ordering.

    You can use ``visible`` to flag the column as hidden by default.
    However, this can be overridden by the ``visibility`` argument to the
    table constructor. If you want to make the column completely unavailable
    to the user, set ``inaccessible`` to True.

    Setting ``sortable`` to False will result in this column being unusable
    in ordering.
    """
    # Tracks each time a Column instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, verbose_name=None, name=None, default=None,
                 visible=True, inaccessible=False, sortable=True):
        self.verbose_name = verbose_name
        self.name = name
        self.default = default
        self.visible = visible
        self.inaccessible = inaccessible
        self.sortable = sortable

        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

class TextColumn(Column):
    pass

class NumberColumn(Column):
    pass