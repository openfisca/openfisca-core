 # -*- coding: utf-8 -*-
#
# Copyright © 2009-2011 Pierre Raybaut
# Licensed under the terms of the MIT License
# (see spyderlib/__init__.py for details)

"""
openfisca GUI-related configuration management
(for non-GUI configuration, see src/baseconfig.py)

Important note regarding shortcuts:
    For compatibility with QWERTZ keyboards, one must avoid using the following
    shortcuts:
        Ctrl + Alt + Q, W, F, G, Y, X, C, V, B, N
"""

import os
import sys
import os.path as osp

from src.qt.QtGui import QLabel, QIcon, QPixmap, QFont, QFontDatabase

# Local import
from src.core.userconfig import UserConfig, get_home_dir, NoDefault
from src.core.baseconfig import (SUBFOLDER, get_module_data_path, _)

SANS_SERIF = ['Sans Serif', 'DejaVu Sans', 'Bitstream Vera Sans',
              'Bitstream Charter', 'Times', 'Lucida Grande', 'Calibri',
              'MS Shell Dlg 2', 'Verdana', 'Geneva', 'Lucid', 'Arial',
              'Helvetica', 'Avant Garde', 'sans-serif']

MONOSPACE = ['Monospace', 'DejaVu Sans Mono', 'Consolas', 'Monaco',
             'Bitstream Vera Sans Mono', 'Andale Mono', 'Liberation Mono',
             'Courier New', 'Courier', 'monospace', 'Fixed', 'Terminal']

if sys.platform == 'darwin':
    BIG = MEDIUM = SMALL = 12
elif os.name == 'nt':
    BIG = 12    
    MEDIUM = 10
    SMALL = 9
else:
    BIG = 12    
    MEDIUM = 9
    SMALL = 9

# Extensions supported by Openfisca
EDIT_FILETYPES = (
    (_("Python files"), ('.py', '.pyw', '.ipy')),
    (_("Cython/Pyrex files"), ('.pyx', '.pxd', '.pxi')),
    (_("C files"), ('.c', '.h')),
    (_("C++ files"), ('.cc', '.cpp', '.cxx', '.h', '.hh', '.hpp', '.hxx')),
    (_("OpenCL files"), ('.cl', )),
    (_("Fortran files"), ('.f', '.for', '.f77', '.f90', '.f95', '.f2k')),
    (_("Patch and diff files"), ('.patch', '.diff', '.rej')),
    (_("Batch files"), ('.bat', '.cmd')),
    (_("Text files"), ('.txt',)),
    (_("reStructured Text files"), ('.txt', '.rst')),
    (_("gettext files"), ('.po', '.pot')),
    (_("Web page files"), ('.css', '.htm', '.html',)),
    (_("Configuration files"), ('.properties', '.session', '.ini', '.inf',
                                '.reg', '.cfg', '.desktop')),
    (_("Composiiton"), ('.ofct',)),
                 )

def _get_filters(filetypes):
    filters = []
    for title, ftypes in filetypes:
        filters.append("%s (*%s)" % (title, " *".join(ftypes)))
    filters.append("%s (*)" % _("All files"))
    return ";;".join(filters)

def _get_extensions(filetypes):
    ftype_list = []
    for _title, ftypes in filetypes:
        ftype_list += list(ftypes)
    return ftype_list

EDIT_FILTERS = _get_filters(EDIT_FILETYPES)
EDIT_EXT = _get_extensions(EDIT_FILETYPES)+['']

# Extensions supported by Spyder's Variable explorer
#IMPORT_EXT = iofuncs.iofunctions.load_extensions.values()

# Extensions that should be visible in Spyder's file/project explorers
SHOW_EXT = ['.png', '.ico', '.svg']

# Extensions supported by Spyder (Editor or Variable explorer)
VALID_EXT = EDIT_EXT  #+IMPORT_EXT

# Find in files include/exclude patterns
INCLUDE_PATTERNS = [r'|'.join(['\\'+_ext+r'$' for _ext in EDIT_EXT if _ext])+\
                    r'|README|INSTALL',
                    r'\.pyw?$|\.ipy$|\.txt$|\.rst$',
                    '.']
EXCLUDE_PATTERNS = [r'\.pyc$|\.pyo$|\.orig$|\.hg|\.svn|build',
                    r'\.pyc$|\.pyo$|\.orig$|\.hg|\.svn']

# Name filters for file/project explorers (excluding files without extension)
NAME_FILTERS = ['*' + _ext for _ext in VALID_EXT + SHOW_EXT if _ext]+\
               ['README', 'INSTALL', 'LICENSE', 'CHANGELOG']

DEFAULTS = [
            ('main',
             {
              'vertical_dockwidget_titlebars': False,
              'vertical_tabs': False,
              'animated_docks': True,
              'window/size': (1260, 740),
              'window/position': (10, 10),
              'window/is_maximized': False,
              'window/is_fullscreen': False,
              'window/prefs_dialog_size': (745, 411),
              'lightwindow/size': (650, 400),
              'lightwindow/position': (30, 30),
              'lightwindow/is_maximized': False,
              'lightwindow/is_fullscreen': False,
              'memory_usage/enable': True,
              'memory_usage/timeout': 2000,
              'cpu_usage/enable': True,
              'cpu_usage/timeout': 2000,
              }),    
            ('quick_layouts',
             {
              'place_holder': '',
              }),       
            ('composition', 
             {
              'year': '2006',
              'nmen': 101,
              'xaxis':  'sal',
              'minrev': 0,
              'maxrev': 50000,
              'import_dir': 'france/castypes',
              'export_dir': 'france/castypes',
              'reform': 'False',
              'graph/enable': 'True',
              'graph/legend/enable': 'True',
              'graph/legend/location': '2',
              'graph/export_dir' : os.path.expanduser('~'),
              'table/enable': 'True',
              'table/format': 'xls',
              'table/export_dir' : os.path.expanduser('~'),
              }),
            ('survey', 
             {
              'enable': 'True',
              'data_file':'france/data/survey.h5',
              'reform': 'False',
              }),            
            ('calibration', 
             {'inputs_filename': 'calage_men.csv',
              'pfam_filename': 'calage_pfam.csv',
              'method': 'logit',
              'up': 3.0,
              'invlo': 3.0,
              'calib_dir' : 'france/calibrations', 
              }),
            ('parameters',
             {
              'enable': 'True',
              'country': 'france',
              'datesim': '2006-01-01',
              'reformes_dir': 'france/reformes',  
#              'file/param': 'param'
              }),
            ('aggregates',
             {
              'enable': 'True',
              'show_dep': 'True',
              'show_benef': 'True',
              'show_real': 'True',
              'show_diff': 'True',
              'show_diff_rel': 'True',
              'show_diff_abs': 'True',
              'show_default': 'True',
              'table/format': 'xls',
              'table/export_dir': os.path.expanduser('~'),
              }),
            ('distribution',
             {
              'enable': 'True',
              'byvar' : 'so',
              'colvar' : 'nivvie'
              }),
            ('inequality',
             {
              'enable': 'True',
              }),
            ]

DEV = not __file__.startswith(sys.prefix)
DEV = False
CONF = UserConfig('openfisca', defaults=DEFAULTS, load=(not DEV), version='2.4.0',
                  subfolder=SUBFOLDER, backup=True, raw_mode=True)
# Removing old .spyder.ini location:
old_location = osp.join(get_home_dir(), '.openfisca.ini')
if osp.isfile(old_location):
    os.remove(old_location)


IMG_PATH = []
def add_image_path(path):
    if not osp.isdir(path):
        return
    global IMG_PATH
    IMG_PATH.append(path)
    for _root, dirs, _files in os.walk(path):
        for dir in dirs:
            IMG_PATH.append(osp.join(path, dir))

add_image_path(get_module_data_path('src', relpath='images'))

# TODO: from spyderlib.otherplugins import PLUGIN_PATH
PLUGIN_PATH = None
if PLUGIN_PATH is not None:
    add_image_path(osp.join(PLUGIN_PATH, 'images'))


def get_image_path(name, default="not_found.png"):
    """Return image absolute path"""
    for img_path in IMG_PATH:
        full_path = osp.join(img_path, name)
        if osp.isfile(full_path):
            return osp.abspath(full_path)
    if default is not None:
        return osp.abspath(osp.join(img_path, default))

def get_icon( name, default=None ):
    """Return image inside a QIcon object"""
    if default is None:
        return QIcon(get_image_path(name))
    elif isinstance(default, QIcon):
        icon_path = get_image_path(name, default=None)
        return default if icon_path is None else QIcon(icon_path)
    else:
        return QIcon(get_image_path(name, default))

def get_image_label( name, default="not_found.png" ):
    """Return image inside a QLabel object"""
    label = QLabel()
    label.setPixmap(QPixmap(get_image_path(name, default)))
    return label

def font_is_installed(font):
    """Check if font is installed"""
    return [fam for fam in QFontDatabase().families() if unicode(fam)==font]
    
def get_family(families):
    """Return the first installed font family in family list"""
    if not isinstance(families, list):
        families = [ families ]
    for family in families:
        if font_is_installed(family):
            return family
    else:
        print "Warning: None of the following fonts is installed: %r" % families
        return QFont().family()
    
FONT_CACHE = {}
def get_font(section, option=None):
    """Get console font properties depending on OS and user options"""
    font = FONT_CACHE.get((section, option))
    if font is None:
        if option is None:
            option = 'font'
        else:
            option += '/font'
        families = CONF.get(section, option+"/family", None)
        if families is None:
            return QFont()
        family = get_family(families)
        weight = QFont.Normal
        italic = CONF.get(section, option+'/italic', False)
        if CONF.get(section, option+'/bold', False):
            weight = QFont.Bold
        size = CONF.get(section, option+'/size', 9)
        font = QFont(family, size, weight)
        font.setItalic(italic)
        FONT_CACHE[(section, option)] = font
    return font

def set_font(font, section, option=None):
    """Set font"""
    if option is None:
        option = 'font'
    else:
        option += '/font'
    CONF.set(section, option+'/family', unicode(font.family()))
    CONF.set(section, option+'/size', float(font.pointSize()))
    CONF.set(section, option+'/italic', int(font.italic()))
    CONF.set(section, option+'/bold', int(font.bold()))
    FONT_CACHE[(section, option)] = font


def get_shortcut(context, name, default=NoDefault):
    """Get keyboard shortcut (key sequence string)"""
    return CONF.get('shortcuts', '%s/%s' % (context, name), default=default)

def set_shortcut(context, name, keystr):
    """Set keyboard shortcut (key sequence string)"""
    CONF.set('shortcuts', '%s/%s' % (context, name), keystr)
    
def iter_shortcuts():
    """Iterate over keyboard shortcuts"""
    for option in CONF.options('shortcuts'):
        context, name = option.split("/", 1)
        yield context, name, get_shortcut(context, name)
        
def reset_shortcuts():
    """Reset keyboard shortcuts to default values"""
    CONF.remove_section('shortcuts')


from spyderlib.widgets.sourcecode.syntaxhighlighters import (
                                COLOR_SCHEME_KEYS, COLOR_SCHEME_NAMES, COLORS)
def get_color_scheme(name):
    """Get syntax color scheme"""
    color_scheme = {}
    for key in COLOR_SCHEME_KEYS:
        color_scheme[key] = CONF.get("color_schemes", "%s/%s" % (name, key))
    return color_scheme

def set_color_scheme(name, color_scheme, replace=True):
    """Set syntax color scheme"""
    section = "color_schemes"
    names = CONF.get("color_schemes", "names", [])
    for key in COLOR_SCHEME_KEYS:
        option = "%s/%s" % (name, key)
        value = CONF.get(section, option, default=None)
        if value is None or replace or name not in names:
            CONF.set(section, option, color_scheme[key])
    names.append(unicode(name))
    CONF.set(section, "names", sorted(list(set(names))))

def set_default_color_scheme(name, replace=True):
    """Reset color scheme to default values"""
    assert name in COLOR_SCHEME_NAMES
    set_color_scheme(name, COLORS[name], replace=replace)

for _name in COLOR_SCHEME_NAMES:
    set_default_color_scheme(_name, replace=False)
CUSTOM_COLOR_SCHEME_NAME = "Custom"
set_color_scheme(CUSTOM_COLOR_SCHEME_NAME, COLORS["Spyder"], replace=False)
