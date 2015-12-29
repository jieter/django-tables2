# coding: utf-8
# pylint: disable=W0611
from .tables import Table
from .columns import (BooleanColumn, Column, CheckBoxColumn, DateColumn,
                      DateTimeColumn, EmailColumn, FileColumn, LinkColumn,
                      TemplateColumn, URLColumn, TimeColumn)
from .config import RequestConfig
from .utils import A
try:
    from .views import SingleTableMixin, SingleTableView
except ImportError:
    pass


__version__ = "1.0.6"
