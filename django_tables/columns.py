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
    does provide ``None`` for a row, the default will be used instead. Note
    that whether this effects ordering might depend on the table type (model
    or normal). Also, you can specify a callable, which will be passed a
    ``BoundRow`` instance and is expected to return the default to be used.

    Additionally, you may specify ``data``. It works very much like
    ``default``, except it's effect does not depend on the actual cell
    value. When given a function, it will always be called with a row object,
    expected to return the cell value. If given a string, that name will be
    used to read the data from the source (instead of the column's name).

    Note the interaction with ``default``. If ``default`` is specified as
    well, it will be used whenver ``data`` yields in a None value.

    You can use ``visible`` to flag the column as hidden by default.
    However, this can be overridden by the ``visibility`` argument to the
    table constructor. If you want to make the column completely unavailable
    to the user, set ``inaccessible`` to True.

    Setting ``sortable`` to False will result in this column being unusable
    in ordering. You can further change the *default* sort direction to
    descending using ``direction``. Note that this option changes the actual
    direction only indirectly. Normal und reverse order, the terms
    django-tables exposes, now simply mean different things.
    """

    ASC = 1
    DESC = 2

    # Tracks each time a Column instance is created. Used to retain order.
    creation_counter = 0

    def __init__(self, verbose_name=None, name=None, default=None, data=None,
                 visible=True, inaccessible=False, sortable=None,
                 direction=ASC):
        self.verbose_name = verbose_name
        self.name = name
        self.default = default
        self.data = data
        if callable(self.data):
            raise DeprecationWarning(('The Column "data" argument may no '+
                                      'longer be a callable. Add  a '+
                                      '``render_%s`` method to your '+
                                      'table instead.') % (name or 'FOO'))
        self.visible = visible
        self.inaccessible = inaccessible
        self.sortable = sortable
        self.direction = direction

        self.creation_counter = Column.creation_counter
        Column.creation_counter += 1

    def _set_direction(self, value):
        if isinstance(value, basestring):
            if value in ('asc', 'desc'):
                self._direction = (value == 'asc') and Column.ASC or Column.DESC
            else:
                raise ValueError('Invalid direction value: %s' % value)
        else:
            self._direction = value

    direction = property(lambda s: s._direction, _set_direction)


class TextColumn(Column):
    pass

class NumberColumn(Column):
    pass