# -*- coding: utf-8 -*-

from __future__ import unicode_literals, print_function, division, absolute_import


extensions = [
    'sphinx.ext.autodoc',
    'sphinxarg.ext',
    'sphinxcontrib.httpdomain',
    ]
master_doc = 'index'
project = 'openfisca-core'
author = 'Openfisca Team'
html_theme = 'classic'
html_static_path = ['_static']
html_context = {
    'css_files': ['_static/css/custom.css']
    }
autoclass_content = 'both'
