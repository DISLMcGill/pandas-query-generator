import os
import sys

sys.path.insert(0, os.path.abspath('../../'))

project = 'pqg'
copyright = '2024, Liam Scalzulli'
author = 'Liam Scalzulli'
extensions = ['sphinx.ext.autodoc', 'sphinx.ext.napoleon', 'sphinx.ext.viewcode']
templates_path = ['_templates']
exclude_patterns = []
html_theme = 'alabaster'
html_static_path = ['_static']
