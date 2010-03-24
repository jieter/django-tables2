import copy
from base import BaseTable, BoundRow


__all__ = ('MemoryTable', 'Table',)


def sort_table(data, order_by):
    """Sort a list of dicts according to the fieldnames in the
    ``order_by`` iterable. Prefix with hypen for reverse.

    Dict values can be callables.
    """
    def _cmp(x, y):
        for name, reverse in instructions:
            lhs, rhs = x.get(name), y.get(name)
            res = cmp((callable(lhs) and [lhs(x)] or [lhs])[0],
                      (callable(rhs) and [rhs(y)] or [rhs])[0])
            if res != 0:
                return reverse and -res or res
        return 0
    instructions = []
    for o in order_by:
        if o.startswith('-'):
            instructions.append((o[1:], True,))
        else:
            instructions.append((o, False,))
    data.sort(cmp=_cmp)


class MemoryTable(BaseTable):

    # This is a separate class from BaseTable in order to abstract the way
    # self.columns is specified.

    def _build_snapshot(self):
        """Rebuilds the table whenever it's options change.

        Whenver the table options change, e.g. say a new sort order,
        this method will be asked to regenerate the actual table from
        the linked data source.

        In the case of this base table implementation, a copy of the
        source data is created, and then modified appropriately.

        # TODO: currently this is called whenever data changes; it is
        # probably much better to do this on-demand instead, when the
        # data is *needed* for the first time.
        """

        # reset caches
        self._columns._reset()
        self._rows._reset()

        snapshot = copy.copy(self._data)
        for row in snapshot:
            # add data that is missing from the source. we do this now so
            # that the colunn ``default`` and ``data`` values can affect
            # sorting (even when callables are used)!
            # This is a design decision - the alternative would be to
            # resolve the values when they are accessed, and either do not
            # support sorting them at all, or run the callables during
            # sorting.
            for column in self.columns.all():
                name_in_source = column.declared_name
                if column.column.data:
                    if callable(column.column.data):
                        # if data is a callable, use it's return value
                        row[name_in_source] = column.column.data(BoundRow(self, row))
                    else:
                        name_in_source = column.column.data

                # the following will be True if:
                #  * the source does not provide that column or provides None
                #  * the column did provide a data callable that returned None
                if row.get(name_in_source, None) is None:
                    row[name_in_source] = column.get_default(BoundRow(self, row))

        if self.order_by:
            actual_order_by = self._resolve_sort_directions(self.order_by)
            sort_table(snapshot, self._cols_to_fields(actual_order_by))
        return snapshot


class Table(MemoryTable):
    def __new__(cls, *a, **kw):
        from warnings import warn
        warn('"Table" has been renamed to "MemoryTable". Please use the '+
             'new name.', DeprecationWarning)
        return MemoryTable.__new__(cls)
