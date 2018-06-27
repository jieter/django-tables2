# coding: utf-8
import os
import re
import sys

import sphinx_rtd_theme

from recommonmark.parser import CommonMarkParser

os.environ["DJANGO_SETTINGS_MODULE"] = "example.settings"

# import project
sys.path.insert(0, os.path.abspath("../"))

project = "django-tables2"
with open("../django_tables2/__init__.py", "rb") as f:
    release = str(re.search('__version__ = "(.+?)"', f.read().decode("utf-8")).group(1))
version = release.rpartition(".")[0]


default_role = "py:obj"

# allow markdown to be able to include the CHANGELOG.md
source_parsers = {".md": CommonMarkParser}
source_suffix = [".rst", ".md"]

# symlink CHANGELOG.md from repo root to the pages dir.
basedir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
filename = "CHANGELOG.md"
target = os.path.join(basedir, "docs", "pages", filename)
if not os.path.islink(target):
    os.symlink(os.path.join(basedir, filename), target)

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinxcontrib.spelling",
]

intersphinx_mapping = {
    "python": ("http://docs.python.org/dev/", None),
    "django": (
        "http://docs.djangoproject.com/en/stable/",
        "http://docs.djangoproject.com/en/stable/_objects/",
    ),
}


master_doc = "index"

html_theme = "sphinx_rtd_theme"
html_theme_path = [sphinx_rtd_theme.get_html_theme_path()]
html_static_path = ["_static"]

# -- Options for Spelling output ------------------------------------------

# String specifying the language, as understood by PyEnchant and enchant.
# Defaults to en_US for US English.
spelling_lang = "en_US"

# String specifying a file containing a list of words known to be spelled
# correctly but that do not appear in the language dictionary selected by
# spelling_lang. The file should contain one word per line.
spelling_word_list_filename = "spelling_wordlist.txt"

# Boolean controlling whether suggestions for misspelled words are printed.
# Defaults to False.
spelling_show_suggestions = True
