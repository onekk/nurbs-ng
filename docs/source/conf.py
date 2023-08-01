"""Sphinx init."""
# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup -------------------------------------------------------------

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "freecad", "nurbswb")))
sys.path.insert(0, os.path.abspath(os.path.join("..", "..", "freecad")))
sys.path.insert(0, os.path.abspath(os.path.join("..", "..")))

# This will fix some warnings, use with care as it is hardcoded and may fail
sys.path.insert(0, os.path.abspath("/usr/lib/freecad/lib/"))
# sys.path.insert(0, os.path.abspath("/usr/lib/freecad/Ext/"))

# debug path when run if needed uncomment.
#print(sys.path)

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'Nurbs WB - Next Generation'
copyright = '2023, Carlo Dormeletti'
author = 'Carlo Dormeletti'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    ]

templates_path = ['_templates']
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']

