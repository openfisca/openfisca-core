# -*- coding: utf-8 -*-

extensions = [
    'sphinx.ext.autodoc',
    'sphinxarg.ext',
    'sphinxcontrib.httpdomain',
    ]
master_doc = 'index'
project = u'openfisca-core'
author = u'Openfisca Team'
html_theme = 'classic'
html_static_path = ['_static']
html_context = {
    'css_files': ['_static/css/custom.css']
    }
