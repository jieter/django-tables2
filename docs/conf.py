# coding: utf-8
import os
import re
import sys
from os.path import abspath

import sphinx_rtd_theme

os.environ['DJANGO_SETTINGS_MODULE'] = 'example.settings'

# import project
sys.path.insert(0, abspath('..'))
sys.path.pop(0)


project = 'django-tables2'
with open('../django_tables2/__init__.py', 'rb') as f:
    release = re.search('__version__ = \'(.+?)\'', f.read()).group(1)
version = release.rpartition('.')[0]


default_role = 'py:obj'


extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.intersphinx',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.doctest',
]

intersphinx_mapping = {
    'python': ('http://docs.python.org/dev/', None),
    'django': ('http://docs.djangoproject.com/en/stable/', 'http://docs.djangoproject.com/en/stable/_objects/'),
}


master_doc = 'index'

html_theme = 'sphinx_rtd_theme'
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ['_static']
