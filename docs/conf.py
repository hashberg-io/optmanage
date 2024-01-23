# pylint: disable = all
# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#

from __future__ import annotations

import inspect
import json
import os
import sys
sys.path.insert(0, os.path.abspath('..'))
import sphinx_rtd_theme # type: ignore

# -- Project information -----------------------------------------------------

project = 'optmanage'
copyright = '2023, Hashberg'
author = 'Hashberg'


# The version info for the project you"re documenting, acts as replacement for
# |version| and |release|, also used in various other places throughout the
# built documents.
#
# The full version, including alpha/beta/rc tags.
release = "1.0.0"
# The short X.Y version.
version = "1.0.0"


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.mathjax',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme',
    'sphinx.ext.viewcode',
    'autodoc_typehints',
]

nitpicky = True                  # warn about every broken reference
add_function_parentheses = False # no parentheses after function names
add_module_names = False         # no module names at start of classes
set_type_checking_flag = False   # setting to True creates issues when dealing with circular dependencies introduced for static typechecking
autodoc_typehints = "none"       # don't document type hints, extension 'autodoc_typehints' will take care of it

with open("autodoc-type-aliases.json", "r") as f:
    autodoc_type_aliases = json.load(f) # load type aliases generated by make-api.py

intersphinx_mapping = {
    'python': ('https://docs.python.org/3', "./intersphinx/python-objects.inv"),
    'typing_validation': ('https://typing-validation.readthedocs.io/en/latest', "./intersphinx/typing-validation-objects.inv"),
    'typed_descriptors': ('https://typed-descriptors.readthedocs.io/en/latest', "./intersphinx/typed-descriptors-objects.inv"),
    'numpy': ('https://numpy.org/doc/stable/', "./intersphinx/numpy-objects.inv"),
    'scipy': ('https://scipy.github.io/devdocs/', "./intersphinx/scipy-objects.inv"),
    'pandas': ('https://pandas.pydata.org/docs/', "./intersphinx/pandas-objects.inv"),
    'networkx': ('https://networkx.org/documentation/stable/', "./intersphinx/networkx-objects.inv"),
    'matplotlib': ('https://matplotlib.org/stable/', "./intersphinx/matplotlib-objects.inv"),
    'sympy': ('https://docs.sympy.org/latest/', "./intersphinx/sympy-objects.inv"),
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = [
    "test"
]

# The name of the Pygments (syntax highlighting) style to use.
pygments_style = 'sphinx'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx.addnodes import pending_xref
from typing import Any

skip_missing_references: set[str] = set()

def on_missing_reference(app: Sphinx, env: BuildEnvironment, node: pending_xref, contnode: Any) -> Any:
    if node['reftarget'] in skip_missing_references:
        return contnode
    else:
        return None

def setup(app: Sphinx) -> None:
    app.connect('missing-reference', on_missing_reference)
