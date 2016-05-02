# coding: utf-8
from .tables import Table
from .columns import (BooleanColumn, Column, CheckBoxColumn, DateColumn,
                      DateTimeColumn, EmailColumn, FileColumn, LinkColumn,
                      RelatedLinkColumn, TemplateColumn, TimeColumn, URLColumn)
from .config import RequestConfig
from .utils import A
from .views import SingleTableMixin, SingleTableView


__version__ = '1.1.8'
