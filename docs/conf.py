import os
import re
import sys
from pathlib import Path

import sphinx_rtd_theme

os.environ["DJANGO_SETTINGS_MODULE"] = "example.settings"

# import project
sys.path.insert(0, str(Path("../").resolve()))

project = "django-tables2"
with open("../django_tables2/__init__.py", "rb") as f:
    release = str(re.search('__version__ = "(.+?)"', f.read().decode()).group(1))
version = release.rpartition(".")[0]


default_role = "py:obj"

# symlink CHANGELOG.md from repo root to the pages dir.
basedir = Path(__file__).parent.parent
filename = "CHANGELOG.md"
target = basedir / "docs" / "pages" / filename
if not target.is_symlink():
    target.symlink_to(basedir / filename)

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.viewcode",
    "sphinx.ext.doctest",
    "sphinxcontrib.spelling",
    "myst_parser",
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

myst_heading_anchors = 3
