# coding: utf-8
from .tables import Table
from .columns import (Column, CheckBoxColumn, DateColumn, DateTimeColumn,
                      LinkColumn, TemplateColumn, EmailColumn, URLColumn)
from .config import RequestConfig
from .utils import A, Attrs
from .views import SingleTableMixin, SingleTableView
__version__ = "0.11.0"
