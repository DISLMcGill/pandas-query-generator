import os
import sys

sys.path.insert(0, os.path.abspath('../..'))

project = 'pqg'
copyright = '2024, Liam Scalzulli'
author = 'Liam Scalzulli'

extensions = [
  'sphinx.ext.autodoc',
  'sphinx.ext.napoleon',
  'sphinx.ext.viewcode',
  'sphinx.ext.intersphinx',
]

templates_path = ['_templates']
exclude_patterns = []

html_absolute_paths = True
html_static_path = ['_static']
html_theme = 'alabaster'
html_use_index = True
html_use_modindex = True
html_use_permalink = True

html_theme_options = {
  'github_banner': True,
  'github_repo': 'pandas-query-generator',
  'github_user': 'DISLMcGill',
  'note_bg': '#FFF59C',
  'show_related': False,
}

numfig = True
numfig_format = {
  'figure': 'Figure %s',
  'table': 'Table %s',
  'code-block': 'Listing %s',
}
