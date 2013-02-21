# -*- coding:utf-8 -*-
#
# This file is part of OpenFisca.
# OpenFisca is a socio-fiscal microsimulation software
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul
# Licensed under the terms of the GVPLv3 or later license
# (see openfisca/__init__.py for details)

# This file is inspired by Spyder, see openfisca/spyder.txt for more details

"""
OpenFisca
=========

Developed and maintained by Mahdi Ben Jelloul and Clément Schaff 

"""

import os
import sys
import os.path as osp
import platform
import re

# Keeping a reference to the original sys.exit before patching it
ORIGINAL_SYS_EXIT = sys.exit
from src.gui.utils.programs import is_module_installed

if is_module_installed('IPython.frontend.qt', '>=0.13'):
    # Importing IPython will eventually set the QT_API environment variable
    import IPython  #@UnresolvedImport #@UnusedImport
    if os.environ.get('QT_API', 'pyqt') == 'pyqt':
        # If PyQt is the selected GUI toolkit (at this stage, only the
        # bootstrap script has eventually set this option), switch to 
        # PyQt API #2 by simply importing the IPython qt module
        os.environ['QT_API'] = 'pyqt'
        try:
            from IPython.external import qt  #analysis:ignore 
        except ImportError:
            # Avoid raising any error here: the spyderlib.requirements module
            # will take care of it, in a user-friendly way (Tkinter message box
            # if no GUI toolkit is installed)
            pass
        
## Check requirements
from src.gui import requirements
requirements.check_path()
requirements.check_qt()
#
## Windows platforms only: support for hiding the attached console window
set_attached_console_visible = None
is_attached_console_visible = None
if os.name == 'nt':
    from src.gui.utils.windows import (set_attached_console_visible,
                                         is_attached_console_visible)


from src.gui.qt.QtGui import (QApplication, QMainWindow, QSplashScreen,
                                QPixmap, QMessageBox, QMenu, QColor, QShortcut,
                                QKeySequence, QDockWidget, QAction,
                                QDesktopServices)

from src.gui.qt.QtCore import SIGNAL, SLOT, QPoint, Qt, QSize, QByteArray, QUrl
from src.gui.qt.compat import (from_qvariant, getopenfilename,
                                 getsavefilename)
# Avoid a "Cannot mix incompatible Qt library" error on Windows platforms 
# when PySide is selected by the QT_API environment variable and when PyQt4 
# is also installed (or any other Qt-based application prepending a directory
# containing incompatible Qt DLLs versions in PATH):
from src.gui.qt import QtSvg  # analysis:ignore

# Local imports
from src import __version__, __project_url__, __forum_url__
from src.gui.utils import encoding, vcs, programs
try:
    from src.utils.environ import WinUserEnvDialog
except ImportError:
    WinUserEnvDialog = None  # analysis:ignore
#from src.widgets.pathmanager import PathManager #TODO

from src.gui.spyder_widgets.status import MemoryStatus, CPUStatus
from src.plugins.general.configdialog import (ConfigDialog, MainConfigPage,
                                            ColorSchemeConfigPage)
from src.plugins.general.shortcuts import ShortcutsConfigPage


try:
    # Assuming Qt >= v4.4
    from src.plugins.general.onlinehelp import OnlineHelp
except ImportError:
    # Qt < v4.4
    OnlineHelp = None  # analysis:ignore


from src.lib.utils import of_import
from src.lib.simulation import SurveySimulation, ScenarioSimulation

from src.plugins.general.Parametres import ParamWidget
from src.plugins.scenario.graph import ScenarioGraphWidget
from src.plugins.scenario.table import ScenarioTableWidget
from src.plugins.survey.survey_explorer import SurveyExplorerWidget
from src.plugins.survey.aggregates import AggregatesWidget
from src.plugins.survey.distribution import DistributionWidget
from src.plugins.survey.inequality import InequalityWidget
from src.plugins.survey.Calibration import CalibrationWidget

from src.gui.utils.qthelpers import (create_action, add_actions, get_std_icon,
                                       create_module_bookmark_actions,
                                       create_bookmark_action,
                                       create_program_action, DialogManager,
                                       keybinding, qapplication,
                                       create_python_script_action, file_uri)

from src.gui.baseconfig import (get_conf_path, _, get_module_data_path,
                                  get_module_source_path, STDOUT, STDERR)

from src.gui.guiconfig import get_icon, get_image_path, get_shortcut
from src.gui.config import CONF, EDIT_EXT
from src.otherplugins import get_openfiscaplugins_mods
from src.gui.utils.iofuncs import load_session, save_session, reset_session
from src.gui.userconfig import NoDefault, NoOptionError
from src.gui.utils import module_completion

TEMP_SESSION_PATH = get_conf_path('.temp.session.tar')

def get_python_doc_path():
    """
    Return Python documentation path
    (Windows: return the PythonXX.chm path if available)
    """
    if os.name == 'nt':
        doc_path = osp.join(sys.prefix, "Doc")
        if not osp.isdir(doc_path):
            return
        python_chm = [path for path in os.listdir(doc_path)
                      if re.match(r"(?i)Python[0-9]{3}.chm", path)]
        if python_chm:
            return file_uri(osp.join(doc_path, python_chm[0]))
    else:
        vinf = sys.version_info
        doc_path = '/usr/share/doc/python%d.%d/html' % (vinf[0], vinf[1])
    python_doc = osp.join(doc_path, "index.html")
    if osp.isfile(python_doc):
        return file_uri(python_doc)


#==============================================================================
# Openfisca's main window widgets utilities
#==============================================================================

def get_focus_widget_properties():
    """
    Get properties of focus widget
    Returns tuple (widget, properties) where properties is a tuple of
    booleans: (is_console, not_readonly, readwrite_editor)
    """
    widget = QApplication.focusWidget()
    
    try:
        not_readonly = not widget.isReadOnly()
    except:
        not_readonly = False
    console = False
    readwrite_editor = not_readonly and not console
    console = False
    textedit_properties = (console, not_readonly, readwrite_editor)
    return widget, textedit_properties

#TODO: Improve the stylesheet below for separator handles to be visible
#      (in Qt, these handles are by default not visible on Windows!)
STYLESHEET="""
QSplitter::handle {
    margin-left: 4px;
    margin-right: 4px;
}

QSplitter::handle:horizontal {
    width: 1px;
    border-width: 0px;
    background-color: lightgray;
}

QSplitter::handle:vertical {
    border-top: 2px ridge lightgray;
    border-bottom: 2px;
}

QMainWindow::separator:vertical {
    margin-left: 1px;
    margin-top: 25px;
    margin-bottom: 25px;
    border-left: 2px groove lightgray;
    border-right: 1px;
}

QMainWindow::separator:horizontal {
    margin-top: 1px;
    margin-left: 5px;
    margin-right: 5px;
    border-top: 2px groove lightgray;
    border-bottom: 2px;
}
"""

class MainWindow(QMainWindow):
    """
    Openfisca main window
    """
    DOCKOPTIONS = QMainWindow.AllowTabbedDocks|QMainWindow.AllowNestedDocks
    openfisca_path = get_conf_path('.path')
    BOOKMARKS = (
         ('OpenfFisca',
          "http://www.openfsca.fr",
          _("Openfisca"), "OpenFisca22.png"),
        ('PyQt4',
          "http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/pyqt4ref.html",
          _("PyQt4 Reference Guide"), "qt.png"),
         ('PyQt4',
          "http://www.riverbankcomputing.co.uk/static/Docs/PyQt4/html/classes.html",
          _("PyQt4 API Reference"), "qt.png"),
        ('matplotlib', "http://matplotlib.sourceforge.net/contents.html",
          _("Matplotlib documentation"),
          "matplotlib.png"),
                 )
           
    def __init__(self, options=None):
        QMainWindow.__init__(self)
        
        qapp = QApplication.instance()
        self.default_style = str(qapp.style().objectName())
        
        self.dialog_manager = DialogManager()
        
        self.init_workdir = options.working_directory
        self.debug = options.debug

        
        self.debug_print("Start of MainWindow constructor")
        
        self.setStyleSheet(STYLESHEET)

        # Shortcut management data
        self.shortcut_data = []
        
        # Loading Openfisca path
        self.path = []
        self.project_path = []
        if osp.isfile(self.openfisca_path):
            self.path, _x = encoding.readlines(self.openfisca_path)
            self.path = [name for name in self.path if osp.isdir(name)]
        self.remove_path_from_sys_path()
        self.add_path_to_sys_path()
        
        self.load_temp_session_action = create_action(self,
                                        _("Reload last session"),
                                        triggered=lambda:
                                        self.load_session(TEMP_SESSION_PATH))
        self.load_session_action = create_action(self,
                                        _("Load session..."),
                                        None, 'fileopen.png',
                                        triggered=self.load_session,
                                        tip=_("Load Openfisca session"))
        self.save_session_action = create_action(self,
                                        _("Save session and quit..."),
                                        None, 'filesaveas.png',
                                        triggered=self.save_session,
                                        tip=_("Save current session "
                                              "and quit application"))
        
        # Plugins
        self.scenario_simulation = None
        self.survey_simulation = None
        
        self.onlinehelp     = None
        self.parameters     = None
        self.test_case_graph = None 
        self.test_case_table = None
        self.survey_explorer = None
        self.aggregates     = None
        self.distribution   = None
        self.inequality   = None
        self.calibration = None
        self.thirdparty_plugins = []
        
        # Preferences
        self.general_prefs = [MainConfigPage, ShortcutsConfigPage,
                              ColorSchemeConfigPage]
        self.prefs_index = None
        self.prefs_dialog_size = None
        
        # Actions
        self.close_dockwidget_action = None
        self.find_action = None
        self.find_next_action = None
        self.find_previous_action = None
        self.replace_action = None
        self.undo_action = None
        self.redo_action = None
        self.copy_action = None
        self.cut_action = None
        self.paste_action = None
        self.delete_action = None
        self.selectall_action = None
        self.maximize_action = None
        self.fullscreen_action = None
        
        # Menu bars
        self.file_menu = None
        self.file_menu_actions = []
        self.edit_menu = None
        self.edit_menu_actions = []
#        self.search_menu = None
#        self.search_menu_actions = []
        self.run_menu = None
        self.run_menu_actions = []
        self.tools_menu = None
        self.tools_menu_actions = []
        self.external_tools_menu = None # We must keep a reference to this,
        # otherwise the external tools menu is lost after leaving setup method
        self.external_tools_menu_actions = []
        self.view_menu = None
        self.windows_toolbars_menu = None
        self.help_menu = None
        self.help_menu_actions = []
        
        # Status bar widgets
        self.mem_status = None
        self.cpu_status = None
        
        # Toolbars
        self.main_toolbar = None
        self.main_toolbar_actions = []
        self.file_toolbar = None
        self.file_toolbar_actions = []
        self.test_case_toolbar = None
        self.test_case_toolbar_actions = []
        self.survey_toolbar = None
        self.survey_toolbar_actions = []
        
        # Set Window title and icon
        title = "openFisca"
        if self.debug:
            title += " (DEBUG MODE)"
        self.setWindowTitle(title)
        icon_name = 'OpenFisca22.png' # needs an svg icon
        self.setWindowIcon(get_icon(icon_name))
        
        # Showing splash screen
        pixmap = QPixmap(get_image_path('splash.png'), 'png')
        self.splash = QSplashScreen(pixmap)
        font = self.splash.font()
        font.setPixelSize(10)
        self.splash.setFont(font)

        self.splash.show()
        self.set_splash(_("Initializing..."))
        if CONF.get('main', 'current_version', '') != __version__:
            CONF.set('main', 'current_version', __version__)
            # Execute here the actions to be performed only once after
            # each update (there is nothing there for now, but it could 
            # be useful some day...)
        
        # List of satellite widgets (registered in add_dockwidget):
        self.widgetlist = []
        
        # Flags used if closing() is called by the exit() shell command
        self.already_closed = False
        self.is_starting_up = True
        
        self.floating_dockwidgets = []
        self.window_size = None
        self.window_position = None
        self.state_before_maximizing = None
        self.current_quick_layout = None
        self.previous_layout_settings = None
        self.last_plugin = None
        self.fullscreen_flag = None # isFullscreen does not work as expected
        # The following flag remember the maximized state even when 
        # the window is in fullscreen mode:
        self.maximized_flag = None
        
        # Session manager
        self.next_session_name = None
        self.save_session_name = None
        self.apply_settings()
        self.debug_print("End of MainWindow constructor")
        

    def parameters_changed(self):
        """
        Enable refresh test case action
        """
        self.composition.action_compute.setEnabled(True)
        self.survey_explorer.action_compute.setEnabled(True)

        
    def refresh_test_case_plugins(self):
        '''
        Refresh test case plugins after conputation
        '''
        self.test_case_graph.refresh_plugin()
        self.test_case_table.refresh_plugin()

        
    def refresh_survey_plugins(self):
        '''
        Refresh survey plugins after computation
        '''
        if CONF.get('survey', 'enable'):
            for plugin in self.survey_plugins:
                plugin.refresh_plugin()

        
    def debug_print(self, message):
        """
        Debug prints
        """
        if self.debug:
            print >>STDOUT, message
        
    #---- Window setup
    def create_toolbar(self, title, object_name, iconsize=24):
        """
        Create and return toolbar with *title* and *object_name*
        """
        toolbar = self.addToolBar(title)
        toolbar.setObjectName(object_name)
        toolbar.setIconSize( QSize(iconsize, iconsize) )
        return toolbar
    
    def setup(self):
        """Setup main window"""
        self.debug_print("*** Start of MainWindow setup ***")
        
        self.close_dockwidget_action = create_action(self,
                                    _("Close current dockwidget"),
                                    triggered=self.close_current_dockwidget,
                                    context=Qt.ApplicationShortcut)
        self.register_shortcut(self.close_dockwidget_action,
                               "_", "Close dockwidget", "Shift+Ctrl+F4")
        
        _text = _("&Find text")
        self.find_action = create_action(self, _text, icon='find.png',
                                         tip=_text, triggered=self.find,
                                         context=Qt.WidgetShortcut)
        self.register_shortcut(self.find_action, "Editor",
                               "Find text", "Ctrl+F")
        self.find_next_action = create_action(self, _("Find &next"),
              icon='findnext.png', triggered=self.find_next,
              context=Qt.WidgetShortcut)
        self.register_shortcut(self.find_next_action, "Editor",
                               "Find next", "F3")
        self.find_previous_action = create_action(self,
                    _("Find &previous"),
                    icon='findprevious.png', triggered=self.find_previous,
                    context=Qt.WidgetShortcut)
        self.register_shortcut(self.find_previous_action, "Editor",
                               "Find previous", "Shift+F3")
        _text = _("&Replace text")
        self.replace_action = create_action(self, _text, icon='replace.png',
                                        tip=_text, triggered=self.replace,
                                        context=Qt.WidgetShortcut)
        self.register_shortcut(self.replace_action, "Editor",
                               "Replace text", "Ctrl+H")
        def create_edit_action(text, tr_text, icon_name):
            textseq = text.split(' ')
            method_name = textseq[0].lower()+"".join(textseq[1:])
            return create_action(self, tr_text,
                                 shortcut=keybinding(text.replace(' ', '')),
                                 icon=get_icon(icon_name),
                                 triggered=self.global_callback,
                                 data=method_name,
                                 context=Qt.WidgetShortcut)
        self.undo_action = create_edit_action("Undo", _("Undo"),
                                              'undo.png')
        self.redo_action = create_edit_action("Redo", _("Redo"), 'redo.png')
        self.copy_action = create_edit_action("Copy", _("Copy"),
                                              'editcopy.png')
        self.cut_action = create_edit_action("Cut", _("Cut"), 'editcut.png')
        self.paste_action = create_edit_action("Paste", _("Paste"),
                                               'editpaste.png')
        self.delete_action = create_edit_action("Delete", _("Delete"),
                                                'editdelete.png')
        self.selectall_action = create_edit_action("Select All",
                                                   _("Select All"),
                                                   'selectall.png')
        self.edit_menu_actions = [self.undo_action, self.redo_action,
                                  None, self.cut_action, self.copy_action,
                                  self.paste_action, self.delete_action,
                                  None, self.selectall_action]
        self.search_menu_actions = [self.find_action, self.find_next_action,
                                    self.find_previous_action,
                                    self.replace_action]
        self.search_toolbar_actions = [self.find_action,
                                       self.find_next_action,
                                       self.replace_action]


        # Maximize current plugin
        self.maximize_action = create_action(self, '',
                                         triggered=self.maximize_dockwidget)
        self.register_shortcut(self.maximize_action, "_",
                               "Maximize dockwidget", "Ctrl+Alt+Shift+M")
        self.__update_maximize_action()
        
        # Fullscreen mode
        self.fullscreen_action = create_action(self,
                                        _("Fullscreen mode"),
                                        triggered=self.toggle_fullscreen)
        self.register_shortcut(self.fullscreen_action, "_",
                               "Fullscreen mode", "F11")
        self.main_toolbar_actions = [self.maximize_action,
                                     self.fullscreen_action, None]
        
        # Main toolbar
        self.main_toolbar = self.create_toolbar(_("Main toolbar"),
                                                "main_toolbar")
        
        # File menu/toolbar
        self.file_menu = self.menuBar().addMenu(_("&File"))
        self.connect(self.file_menu, SIGNAL("aboutToShow()"),
                     self.update_file_menu)
        self.file_toolbar = self.create_toolbar(_("File toolbar"),
                                                "file_toolbar")
                        
        # Run menu/toolbar
        self.run_menu = self.menuBar().addMenu(_("&Run"))
        self.test_case_toolbar = self.create_toolbar(_("Test case toolbar"),
                                               "test_case_toolbar")
        
        # Tools menu
        self.tools_menu = self.menuBar().addMenu(_("&Tools"))
        
        # View menu
        self.view_menu = self.menuBar().addMenu(_("&View"))
        
        # Help menu
        self.help_menu = self.menuBar().addMenu("?")
                
        # Status bar
        status = self.statusBar()
        status.setObjectName("StatusBar")
        status.showMessage(_("Welcome to Openfisca!"), 5000)
        
        
        # Tools + External Tools
        prefs_action = create_action(self, _("Pre&ferences"),
                                     icon='configure.png',
                                     triggered=self.edit_preferences)
        self.register_shortcut(prefs_action, "_", "Preferences",
                               "Ctrl+Alt+Shift+P")

        update_modules_action = create_action(self,
                                    _("Update module names list"),
                                    None, 'reload.png',
                                    triggered=module_completion.reset,
                                    tip=_("Refresh list of module names "
                                          "available in PYTHONPATH"))
        self.tools_menu_actions = [prefs_action,]
        self.tools_menu_actions += [update_modules_action, None]
        self.main_toolbar_actions += [prefs_action,]
        if WinUserEnvDialog is not None:
            winenv_action = create_action(self,
                    _("Current user environment variables..."),
                    icon='win_env.png',
                    tip=_("Show and edit current user environment "
                          "variables in Windows registry "
                          "(i.e. for all sessions)"),
                    triggered=self.win_env)
            self.tools_menu_actions.append(winenv_action)
        
        # External Tools submenu
        self.external_tools_menu = QMenu(_("External Tools"))
        self.external_tools_menu_actions = []

        # Qt-related tools
        additact = [None]
        for name in ("designer-qt4", "designer"):
            qtdact = create_program_action(self, _("Qt Designer"),
                                           'qtdesigner.png', name)
            if qtdact:
                break
        for name in ("linguist-qt4", "linguist"):
            qtlact = create_program_action(self, _("Qt Linguist"),
                                           'qtlinguist.png', "linguist")
            if qtlact:
                break
        args = ['-no-opengl'] if os.name == 'nt' else []
        qteact = create_python_script_action(self,
                               _("Qt examples"), 'qt.png', "PyQt4",
                               osp.join("examples", "demos",
                                        "qtdemo", "qtdemo"), args)
        for act in (qtdact, qtlact, qteact):
            if act:
                additact.append(act)
        if len(additact) > 1:
            self.external_tools_menu_actions += additact

        # ViTables
        vitables_act = create_program_action(self, _("ViTables"),
                                             'vitables.png', "vitables")
        if vitables_act:
            self.external_tools_menu_actions += [None, vitables_act]
                    
        # Populating file menu entries
        quit_action = create_action(self, _("&Quit"),
                                    icon = 'exit.png', tip=_("Quit"),
                                    triggered = SLOT('close()')
                                    )
        self.register_shortcut(quit_action, "_", "Quit", "Ctrl+Q")
        self.file_menu_actions += [self.load_temp_session_action,
                                   self.load_session_action,
                                   self.save_session_action,
                                   None, quit_action]
        self.set_splash("")

#        self.action_calibrate = create_action(self, u'Caler les poids', shortcut = 'CTRL+K', icon = 'scale22.png', triggered = self.calibrate)
#        self.action_inflate = create_action(self, u'Inflater les montants', shortcut = 'CTRL+I', icon = 'scale22.png', triggered = self.inflate)
                
        # Parameters widget
        if CONF.get('parameters', 'enable'):                
            country = CONF.get('parameters', 'country')
            self.set_splash(_("Loading Parameters..."))
            self.parameters = ParamWidget(self)
            self.parameters.register_plugin()
                                                
        # Test case widgets
        self.scenario_simulation = ScenarioSimulation()
#        self.scenario = self.scenario_simulation.scenario
        CompositionWidget = of_import('widgets.Composition', 'CompositionWidget', country)
        
        self.set_splash(_("Loading Test case composer ..."))
        self.composition = CompositionWidget(self.scenario_simulation, self)
        self.composition.register_plugin()

        # Scenario Graph widget
        if CONF.get('composition', 'graph/enable'):
            self.set_splash(_("Loading ScenarioGraph..."))
            self.test_case_graph = ScenarioGraphWidget(self)
            self.test_case_graph.register_plugin()

        # Scenario Table widget
        if CONF.get('composition', 'table/enable'):
            self.set_splash(_("Loading ScenarioTable..."))
            self.test_case_table = ScenarioTableWidget(self)
            self.test_case_table.register_plugin()
       
        # Survey Widgets
        # SurveyExplorer widget

        self.survey_explorer = SurveyExplorerWidget(self)
        self.set_splash(_("Loading SurveyExplorer..."))
        self.survey_explorer.register_plugin()
        self.survey_plugins = [ self.survey_explorer]
        
        if CONF.get('survey', 'enable') is True:
            #try:
            self.register_survey_widgets(True)
#            except:
#                pass
        # Online help widget
        if CONF.get('onlinehelp', 'enable') and OnlineHelp is not None:
            self.set_splash(_("Loading online help..."))
            self.onlinehelp = OnlineHelp(self)
            self.onlinehelp.register_plugin()
                           
        # ? menu
        about_action = create_action(self,
                                _("About %s...") % "openFisca",
                                icon=get_std_icon('MessageBoxInformation'),
                                triggered=self.about)
        report_action = create_action(self,
                                _("Report issue..."),
                                icon=get_icon('bug.png'),
                                triggered=self.report_issue
                                )
        
        # Spyder documentation
        doc_path = get_module_data_path('src', relpath="doc",
                                        attr_name='DOCPATH')
        # * Trying to find the chm doc
        openfisca_doc = osp.join(doc_path, "Spyderdoc.chm")
        if not osp.isfile(openfisca_doc):
            openfisca_doc = osp.join(doc_path, os.pardir, os.pardir,
                                  "Spyderdoc.chm")
        # * Trying to find the html doc
        if not osp.isfile(openfisca_doc):
            openfisca_doc = osp.join(doc_path, "index.html")
            if not osp.isfile(openfisca_doc):  # development version
                openfisca_doc = osp.join(get_module_source_path("src"),
                                      "doc", "_build", "html", "index.html")
        openfisca_doc = file_uri(openfisca_doc)
        doc_action = create_bookmark_action(self, openfisca_doc,
                           _("Openfisca documentation"), shortcut="F1",
                           icon=get_std_icon('DialogHelpButton'))
        self.help_menu_actions = [about_action, report_action, doc_action]
        
#        # Python documentation
#        if get_python_doc_path() is not None:
#            pydoc_act = create_action(self, _("Python documentation"),
#                              icon=get_icon('python.png'),
#                              triggered=lambda:
#                              programs.start_file(get_python_doc_path()))
#            self.help_menu_actions += [None, pydoc_act]
#        # Qt assistant link
#        qta_act = create_program_action(self, _("Qt Assistant"),
#                                        'qtassistant.png', "assistant")
#        if qta_act:
#            self.help_menu_actions.append(qta_act)
#        # Windows-only: documentation located in sys.prefix/Doc
#        def add_doc_action(text, path):
#            """Add doc action to help menu"""
#            ext = osp.splitext(path)[1]
#            if ext:
#                icon = get_icon(ext[1:]+".png")
#            else:
#                icon = get_std_icon("DirIcon")
#            path = file_uri(path)
#            action = create_action(self, text, icon=icon,
#                   triggered=lambda path=path: programs.start_file(path))
#            self.help_menu_actions.append(action)
#        if os.name == 'nt':
#            sysdocpth = osp.join(sys.prefix, 'Doc')
#            for docfn in os.listdir(sysdocpth):
#                pt = r'([a-zA-Z\_]*)(doc)?(-dev)?(-ref)?(-user)?.(chm|pdf)'
#                match = re.match(pt, docfn)
#                if match is not None:
#                    pname = match.groups()[0]
#                    if pname not in ('Python', ):
#                        add_doc_action(pname, osp.join(sysdocpth, docfn))

        # Online documentation
        web_resources = QMenu(_("Web Resources"))
        web_resources.setIcon(get_icon("browser.png"))
        add_actions(web_resources,
                    create_module_bookmark_actions(self, self.BOOKMARKS))
        self.help_menu_actions.append(web_resources)
        
        # Status bar widgets
        self.mem_status = MemoryStatus(self, status)
        self.cpu_status = CPUStatus(self, status)
        self.apply_statusbar_settings()

        # Third-party plugins
        for mod in get_openfiscaplugins_mods(prefix='p_', extension='.py'):
            try:
                plugin = mod.PLUGIN_CLASS(self)
                self.thirdparty_plugins.append(plugin)
                plugin.register_plugin()
            except AttributeError, error:
                print >>STDERR, "%s: %s" % (mod, str(error))
                            
        # View menu
        self.windows_toolbars_menu = QMenu(_("Windows and toolbars"), self)
        self.connect(self.windows_toolbars_menu, SIGNAL("aboutToShow()"),
                     self.update_windows_toolbars_menu)
        self.view_menu.addMenu(self.windows_toolbars_menu)
        reset_layout_action = create_action(self, _("Reset window layout"),
                                        triggered=self.reset_window_layout)
        quick_layout_menu = QMenu(_("Custom window layouts"), self)
        ql_actions = []
        for index in range(1, 4):
            if index > 0:
                ql_actions += [None]
            qli_act = create_action(self,
                                    _("Switch to/from layout %d") % index,
                                    triggered=lambda i=index:
                                    self.quick_layout_switch(i))
            self.register_shortcut(qli_act, "_",
                                   "Switch to/from layout %d" % index,
                                   "Shift+Alt+F%d" % index)
            qlsi_act = create_action(self, _("Set layout %d") % index,
                                     triggered=lambda i=index:
                                     self.quick_layout_set(i))
            self.register_shortcut(qlsi_act, "_",
                                   "Set layout %d" % index,
                                   "Ctrl+Shift+Alt+F%d" % index)
            ql_actions += [qli_act, qlsi_act]
        add_actions(quick_layout_menu, ql_actions)

        add_actions(self.view_menu, (None, self.maximize_action,
                                     self.fullscreen_action, None,
                                     reset_layout_action, quick_layout_menu,
                                     None, self.close_dockwidget_action))
            
        # Adding external tools action to "Tools" menu
        external_tools_act = create_action(self, _("External Tools"),
                                           icon="ext_tools.png")
        external_tools_act.setMenu(self.external_tools_menu)
        self.tools_menu_actions.append(external_tools_act)
        self.main_toolbar_actions.append(external_tools_act)
            
        # Filling out menu/toolbar entries:
        add_actions(self.file_menu, self.file_menu_actions)

        add_actions(self.run_menu, self.run_menu_actions)
#            add_actions(self.interact_menu, self.interact_menu_actions)

        add_actions(self.tools_menu, self.tools_menu_actions)
        add_actions(self.external_tools_menu,
                    self.external_tools_menu_actions)
        add_actions(self.help_menu, self.help_menu_actions)
        
        add_actions(self.main_toolbar, self.main_toolbar_actions)
        add_actions(self.file_toolbar, self.file_toolbar_actions)
        
        add_actions(self.test_case_toolbar, self.test_case_toolbar_actions)
        if self.survey_toolbar is not None:
            add_actions(self.survey_toolbar, self.survey_toolbar_actions)
        
        
        # Apply all defined shortcuts (plugins + 3rd-party plugins)
        self.apply_shortcuts()
        
        # Emitting the signal notifying plugins that main window menu and 
        # toolbar actions are all defined:
        self.emit(SIGNAL('all_actions_defined()'))
        
        # Window set-up
        self.debug_print("Setting up window...")
        self.setup_layout(default=False)
            
        self.splash.hide()
        
        # Enabling tear off for all menus except help menu
        for child in self.menuBar().children():
            if isinstance(child, QMenu) and child != self.help_menu:
                child.setTearOffEnabled(True)
        
#        # Menu about to show
#        for child in self.menuBar().children():
#            if isinstance(child, QMenu):
#                self.connect(child, SIGNAL("aboutToShow()"),
#                             self.update_edit_menu)



        self.debug_print("*** End of MainWindow setup ***")
        self.is_starting_up = False
 
    def register_survey_widgets(self, boolean = True):
        """
        Registers enabled survey widgets
        """
        
        
        for plugin in self.survey_plugins:
            if plugin is not self.survey_explorer:
                self.removeDockWidget(plugin.dockwidget)

        if boolean is True:
            self.debug_print("Register survey widgets")
            self.survey_simulation = SurveySimulation()
            self.survey_explorer.initialize()
            self.survey_simulation.set_param()


            
            # Calibration widget
            if CONF.get('calibration', 'enable'):
                self.set_splash(_("Loading calibration widget ..."))
                self.calibration = CalibrationWidget(self)
                self.calibration.register_plugin()
                self.survey_plugins  += [ self.calibration]
            # Aggregates widget
            if CONF.get('aggregates', 'enable'):
                self.set_splash(_("Loading aggregates widget ..."))
                self.aggregates = AggregatesWidget(self)
                self.aggregates.register_plugin()
                self.survey_plugins  += [ self.aggregates]
                
            # Distribution widget
            if CONF.get('distribution', 'enable'):
                self.set_splash(_("Loading distribution widget ..."))
                self.distribution = DistributionWidget(self)
                self.distribution.register_plugin()
                self.survey_plugins  += [ self.distribution]
            
            # Inequality widget
            if CONF.get('inequality', 'enable'):
                self.set_splash(_("Loading inequality widget ..."))
                self.inequality = InequalityWidget(self)
                self.inequality.register_plugin()
                self.survey_plugins  += [ self.inequality]

            self.survey_toolbar = self.create_toolbar(_("Survey toolbar"),
                                                      "survey_toolbar")

        
            for first, second in ((self.test_case_table, self.survey_explorer),
                                  (self.survey_explorer, self.aggregates), 
                                  (self.aggregates, self.distribution), 
                                   (self.distribution, self.inequality),
                                   (self.inequality, self.calibration),
                                  ):
                if first is not None and second is not None:
                    self.tabifyDockWidget(first.dockwidget, second.dockwidget)


#            self.update_windows_toolbars_menu()
            
    def post_visible_setup(self):
        """
        Actions to be performed only after the main window's `show` method 
        was triggered
        """
        # [Workaround for Issue 880]
        # QDockWidget objects are not painted if restored as floating 
        # windows, so we must dock them before showing the mainwindow,
        # then set them again as floating windows here.
        for widget in self.floating_dockwidgets:
            widget.setFloating(True)
        # In MacOS X 10.7 our app is not displayed after initialized (I don't
        # know why because this doesn't happen when started from the terminal),
        # so we need to resort to this hack to make it appear.
        if sys.platform == 'darwin':
            if 'Openfisca.app' in __file__:
                import subprocess
                idx = __file__.index('Openfisca.app')
                app_path = __file__[:idx]
                subprocess.call(['open', app_path + 'Openfisca.app'])
        
    def load_window_settings(self, prefix, default=False, section='main'):
        """
        Load window layout settings from userconfig-based configuration
        with *prefix*, under *section*
        default: if True, do not restore inner layout
        """
        get_func = CONF.get_default if default else CONF.get
        window_size = get_func(section, prefix+'size')
        prefs_dialog_size = get_func(section, prefix+'prefs_dialog_size')
        if default:
            hexstate = None
        else:
            hexstate = get_func(section, prefix+'state', None)
        pos = get_func(section, prefix+'position')
        is_maximized =  get_func(section, prefix+'is_maximized')
        is_fullscreen = get_func(section, prefix+'is_fullscreen')
        return hexstate, window_size, prefs_dialog_size, pos, is_maximized, \
               is_fullscreen
    
    def get_window_settings(self):
        """
        Return current window settings
        Symetric to the 'set_window_settings' setter
        """
        size = self.window_size
#        width, height = size.width(), size.height()
        is_fullscreen = self.isFullScreen()
        if is_fullscreen:
            is_maximized = self.maximized_flag
        else:
            is_maximized = self.isMaximized()
        pos = self.window_position
        posx, posy = pos.x(), pos.y()
        hexstate = str(self.saveState().toHex())
        return hexstate, size, posx, posy, is_maximized, is_fullscreen
        
    def set_window_settings(self, hexstate, window_size, prefs_dialog_size,
                            pos, is_maximized, is_fullscreen):
        """
        Set window settings
        Symetric to the 'get_window_settings' accessor
        """
        self.setUpdatesEnabled(False)
        self.window_size = QSize(window_size[0], window_size[1]) # width,height
        self.prefs_dialog_size = QSize(prefs_dialog_size[0],
                                       prefs_dialog_size[1]) # width,height
        self.window_position = QPoint(pos[0], pos[1]) # x,y
        self.setWindowState(Qt.WindowNoState)
        self.resize(self.window_size)
        self.move(self.window_position)

        # Window layout
        if hexstate:
            self.restoreState( QByteArray().fromHex(str(hexstate)) )
            # [Workaround for Issue 880]
            # QDockWidget objects are not painted if restored as floating 
            # windows, so we must dock them before showing the mainwindow.
            for widget in self.children():
                if isinstance(widget, QDockWidget) and widget.isFloating():
                    self.floating_dockwidgets.append(widget)
                    widget.setFloating(False)
        # Is fullscreen?
        if is_fullscreen:
            self.setWindowState(Qt.WindowFullScreen)
        self.__update_fullscreen_action()
        # Is maximized?
        if is_fullscreen:
            self.maximized_flag = is_maximized
        elif is_maximized:
            self.setWindowState(Qt.WindowMaximized)
        self.setUpdatesEnabled(True)
        
    def save_current_window_settings(self, prefix, section='main'):
        """
        Save current window settings with *prefix* in
        the userconfig-based configuration, under *section*
        """
        win_size = self.window_size
        prefs_size = self.prefs_dialog_size
        
        CONF.set(section, prefix+'size', (win_size.width(), win_size.height()))
        CONF.set(section, prefix+'prefs_dialog_size',
                 (prefs_size.width(), prefs_size.height()))
        CONF.set(section, prefix+'is_maximized', self.isMaximized())
        CONF.set(section, prefix+'is_fullscreen', self.isFullScreen())
        pos = self.window_position
        CONF.set(section, prefix+'position', (pos.x(), pos.y()))

        self.maximize_dockwidget(restore=True)# Restore non-maximized layout
        qba = self.saveState()
        CONF.set(section, prefix+'state', str(qba.toHex()))
        CONF.set(section, prefix+'statusbar',
                 not self.statusBar().isHidden())
        
    def setup_layout(self, default=False):
        """
        Setup window layout
        """
        prefix = ('window') + '/'
        (hexstate, window_size, prefs_dialog_size, pos, is_maximized,
         is_fullscreen) = self.load_window_settings(prefix, default)
        
        self.test_case_plugins = [ self.composition, self.test_case_graph, self.test_case_table ]

                
        if hexstate is None:
            # First Spyder execution:
            # trying to set-up the dockwidget/toolbar positions to the best 
            # appearance possible
            splitting = (
                         (self.test_case_graph, self.parameters, Qt.Horizontal),
                         (self.parameters, self.composition, Qt.Vertical),
                         )
            for first, second, orientation in splitting:
                if first is not None and second is not None:
                    self.splitDockWidget(first.dockwidget, second.dockwidget,
                                         orientation)

            for first, second in ((self.test_case_graph, self.test_case_table),
                                   (self.test_case_table, self.aggregates), 
                                   (self.aggregates, self.distribution), 
                                   (self.distribution, self.inequality),
                                   (self.inequality, self.survey_explorer),
                                   (self.survey_explorer, self.calibration),
                                  ):
                if first is not None and second is not None:
                    self.tabifyDockWidget(first.dockwidget, second.dockwidget)
            
            for plugin in [self.onlinehelp, ]+self.thirdparty_plugins:
                if plugin is not None:
                    plugin.dockwidget.close()
            for plugin in self.test_case_plugins + self.survey_plugins:
                if plugin is not None:
                    plugin.dockwidget.raise_()
                    
            if not CONF.get('survey', 'enable'):
                self.survey_explorer.dockwidget.hide()
#            for toolbar in (self.run_toolbar,):
#                toolbar.close()
        
        self.composition.compute()
        self.test_case_graph.dockwidget.raise_()
        
        self.set_window_settings(hexstate,window_size, prefs_dialog_size, pos,
                                 is_maximized, is_fullscreen)

    def reset_window_layout(self):
        """
        Reset window layout to default
        """
        answer = QMessageBox.warning(self, _("Warning"),
                     _("Window layout will be reset to default settings: "
                       "this affects window position, size and dockwidgets.\n"
                       "Do you want to continue?"),
                     QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.setup_layout(default=True)
            
    def quick_layout_switch(self, index):
        """
        Switch to quick layout number *index*
        """
        if self.current_quick_layout == index:
            self.set_window_settings(*self.previous_layout_settings)
            self.current_quick_layout = None
        else:
            try:
                settings = self.load_window_settings('layout_%d/' % index,
                                                     section='quick_layouts')
            except NoOptionError:
                QMessageBox.critical(self, _("Warning"),
                                     _("Quick switch layout #%d has not yet "
                                       "been defined.") % index)
                return
            self.previous_layout_settings = self.get_window_settings()
            self.set_window_settings(*settings)
            self.current_quick_layout = index
    
    def quick_layout_set(self, index):
        """
        Save current window settings as quick layout number *index*
        """
        self.save_current_window_settings('layout_%d/' % index,
                                          section='quick_layouts')

    def plugin_focus_changed(self):
        """
        Focus has changed from one plugin to another
        """
        # self.update_edit_menu()
        # self.update_search_menu()
        
    def update_file_menu(self):
        """
        Update file menu
        """
        self.load_temp_session_action.setEnabled(osp.isfile(TEMP_SESSION_PATH))
#        widget, textedit_properties = get_focus_widget_properties()
#        for widget in self.widgetlist:
#            if widget.isvisible:
#                widget.get_plugin_actions()
#                add_actions(self.file_menu, self.file_menu_actions)
        
    def update_edit_menu(self):
        """
        Update edit menu
        """
        if self.menuBar().hasFocus():
            return
        # Disabling all actions to begin with
#        for child in self.edit_menu.actions():
#            child.setEnabled(False)        
        
        widget, textedit_properties = get_focus_widget_properties()
        if textedit_properties is None: # widget is not an editor/console
            return
        #!!! Below this line, widget is expected to be a QPlainTextEdit instance
        console, not_readonly, readwrite_editor = textedit_properties
        
        # Editor has focus and there is no file opened in it
        if not console and not_readonly and not self.editor.is_file_opened():
            return
        
        self.selectall_action.setEnabled(True)
        
        # Undo, redo
        self.undo_action.setEnabled( readwrite_editor \
                                     and widget.document().isUndoAvailable() )
        self.redo_action.setEnabled( readwrite_editor \
                                     and widget.document().isRedoAvailable() )

        # Copy, cut, paste, delete
        has_selection = widget.has_selected_text()
        self.copy_action.setEnabled(has_selection)
        self.cut_action.setEnabled(has_selection and not_readonly)
        self.paste_action.setEnabled(not_readonly)
        self.delete_action.setEnabled(has_selection and not_readonly)
        
        # Comment, uncomment, indent, unindent...
        if not console and not_readonly:
            # This is the editor and current file is writable
            for action in self.editor.edit_menu_actions:
                action.setEnabled(True)
        
    def update_search_menu(self):
        """
        Update search menu
        """
        if self.menuBar().hasFocus():
            return        
        # Disabling all actions to begin with
        for child in [self.find_action, self.find_next_action,
                      self.find_previous_action, self.replace_action]:
            child.setEnabled(False)
        
        widget, textedit_properties = get_focus_widget_properties()
        for action in self.editor.search_menu_actions:
            action.setEnabled(self.editor.isAncestorOf(widget))
        if textedit_properties is None: # widget is not an editor/console
            return
        #!!! Below this line, widget is expected to be a QPlainTextEdit instance
        _x, _y, readwrite_editor = textedit_properties
        for action in [self.find_action, self.find_next_action,
                       self.find_previous_action]:
            action.setEnabled(True)
        self.replace_action.setEnabled(readwrite_editor)
        self.replace_action.setEnabled(readwrite_editor)
        
    def update_windows_toolbars_menu(self):
        """
        Update windows&toolbars menu
        """
        self.windows_toolbars_menu.clear()
        popmenu = self.createPopupMenu()
        add_actions(self.windows_toolbars_menu, popmenu.actions())
        
    def set_splash(self, message):
        """
        Set splash message
        """
        if message:
            self.debug_print(message)
        self.splash.show()
        self.splash.showMessage(message, Qt.AlignBottom | Qt.AlignCenter | 
                                Qt.AlignAbsolute, QColor(Qt.white))
        QApplication.processEvents()
        
    def closeEvent(self, event):
        """
        closeEvent reimplementation
        """
        if self.closing(True):
            event.accept()
        else:
            event.ignore()
            
    def resizeEvent(self, event):
        """
        Reimplement Qt method
        """
        if not self.isMaximized() and not self.fullscreen_flag:
            self.window_size = self.size()
        QMainWindow.resizeEvent(self, event)
        
    def moveEvent(self, event):
        """
        Reimplement Qt method
        """
        if not self.isMaximized() and not self.fullscreen_flag:
            self.window_position = self.pos()
        QMainWindow.moveEvent(self, event)
        
    def closing(self, cancelable=False):
        """
        Exit tasks
        """
        if self.already_closed or self.is_starting_up:
            return True
        for widget in self.widgetlist:
            if not widget.closing_plugin(cancelable):
                return False
        self.dialog_manager.close_all()
        self.already_closed = True
        return True
        
    def add_dockwidget(self, child):
        """
        Add QDockWidget and toggleViewAction
        """
        self.debug_print('Adding dockwidget ' + str(child)) 
        dockwidget, location = child.create_dockwidget()
        if CONF.get('main', 'vertical_dockwidget_titlebars'):
            dockwidget.setFeatures(dockwidget.features()|
                                   QDockWidget.DockWidgetVerticalTitleBar)
        self.addDockWidget(location, dockwidget)
        self.widgetlist.append(child)
        
    def close_current_dockwidget(self):
        widget = QApplication.focusWidget()
        for plugin in self.widgetlist:
            if plugin.isAncestorOf(widget):
                plugin.dockwidget.hide()
                break
        
    def __update_maximize_action(self):
        if self.state_before_maximizing is None:
            text = _("Maximize current plugin")
            tip = _("Maximize current plugin to fit the whole "
                    "application window")
            icon = "maximize.png"
        else:
            text = _("Restore current plugin")
            tip = _("Restore current plugin to its original size and "
                    "position within the application window")
            icon = "unmaximize.png"
        self.maximize_action.setText(text)
        self.maximize_action.setIcon(get_icon(icon))
        self.maximize_action.setToolTip(tip)
        
    def maximize_dockwidget(self, restore=False):
        """Shortcut: Ctrl+Alt+Shift+M
        First call: maximize current dockwidget
        Second call (or restore=True): restore original window layout"""
        if self.state_before_maximizing is None:
            if restore:
                return
            # No plugin is currently maximized: maximizing focus plugin
            self.state_before_maximizing = self.saveState()
            focus_widget = QApplication.focusWidget()
            for plugin in self.widgetlist:
                plugin.dockwidget.hide()
                if plugin.isAncestorOf(focus_widget):
                    self.last_plugin = plugin
            self.last_plugin.dockwidget.toggleViewAction().setDisabled(True)
            self.setCentralWidget(self.last_plugin)
            self.last_plugin.ismaximized = True
            # Workaround to solve an issue with editor's outline explorer:
            # (otherwise the whole plugin is hidden and so is the outline explorer
            #  and the latter won't be refreshed if not visible)
            self.last_plugin.show()
            self.last_plugin.visibility_changed(True)
        else:
            # Restore original layout (before maximizing current dockwidget)
            self.last_plugin.dockwidget.setWidget(self.last_plugin)
            self.last_plugin.dockwidget.toggleViewAction().setEnabled(True)
            self.setCentralWidget(None)
            self.last_plugin.ismaximized = False
            self.restoreState(self.state_before_maximizing)
            self.state_before_maximizing = None
            self.last_plugin.get_focus_widget().setFocus()
        self.__update_maximize_action()
        
    def __update_fullscreen_action(self):
        if self.isFullScreen():
            icon = "window_nofullscreen.png"
        else:
            icon = "window_fullscreen.png"
        self.fullscreen_action.setIcon(get_icon(icon))
        
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.fullscreen_flag = False
            self.showNormal()
            if self.maximized_flag:
                self.showMaximized()
        else:
            self.maximized_flag = self.isMaximized()
            self.fullscreen_flag = True
            self.showFullScreen()
        self.__update_fullscreen_action()

    def add_to_toolbar(self, toolbar, widget):
        """Add widget actions to toolbar"""
        actions = widget.toolbar_actions
        if actions is not None:
            add_actions(toolbar, actions)

    def about(self):
        """
        About openFisca
        """
        import src.gui.qt.QtCore
        QMessageBox.about(self,
            _("About %s") % "openFisca",
            
          u''' <b>openFisca</b><sup>beta</sup> v %s
              <p> %s
              <p> Copyright &copy; 2011 Clément Schaff, Mahdi Ben Jelloul
              Tout droit réservé
              <p> License GPL version 3 ou supérieure
              <p> Python %s - Qt %s - PyQt %s on %s'''
              % (__version__, __project_url__, platform.python_version(),
                          src.gui.qt.QtCore.__version__, src.gui.qt.__version__, platform.system()))
#                 __project_url__, __forum_url__,
#                 platform.python_version(),
#                 src.gui.qt.QtCore.__version__,
#                 src.gui.qt.API_NAME,
#                 src.gui.qt.__version__,
#                 platform.system()) )

#            """<b>%s %s</b> %s
#            <br>Scientific PYthon Development EnviRonment
#            <p>Copyright &copy; 2009-2012 Pierre Raybaut
#            <br>Licensed under the terms of the MIT License
#            <p>Created by Pierre Raybaut
#            <br>Developed and maintained by the 
#            <a href="%s/people/list">Spyder Development Team</a>
#            <br>Many thanks to all the Spyder beta-testers and regular users.
#            <p>Source code editor: Python code real-time analysis is powered by 
#            %spyflakes %s%s (&copy; 2005 
#            <a href="http://www.divmod.com/">Divmod, Inc.</a>) and other code 
#            introspection features (completion, go-to-definition, ...) are 
#            powered by %srope %s%s (&copy; 2006-2009 Ali Gholami Rudi)
#            <br>Most of the icons are coming from the %sCrystal Project%s 
#            (&copy; 2006-2007 Everaldo Coelho)
#            <p>Spyder's community:
#            <ul><li>Bug reports and feature requests: 
#            <a href="%s">Google Code</a>
#            </li><li>Discussions around the project: 
#            <a href="%s">Google Group</a>
#            </li></ul>
#            <p>This project is part of 
#            <a href="http://www.pythonxy.com">Python(x,y) distribution</a>
#            <p>Python %s, Qt %s, %s %s on %s"""
#            % ("OpenFisca", __version__, 0, __project_url__,
#                 "<span style=\'color: #444444\'><b>",
#                 pyflakes_version,
#                 "</b></span>",
#                 "<span style=\'color: #444444\'><b>",
#                 rope_version,
#                 "</b></span>",
#                 "<span style=\'color: #444444\'><b>",
#                 "</b></span>",
#                 __project_url__, __forum_url__,
#                 platform.python_version(),
#                 src.gui.qt.QtCore.__version__,
#                 src.gui.qt.API_NAME,
#                 src.gui.qt.__version__,
#                 platform.system()) )

    def report_issue(self):
        pass
#        import urllib
#        import spyderlib
#        # Get Mercurial revision for development version
#        revlink = ''
#        spyderpath = spyderlib.__path__[0]
#        if osp.isdir(osp.abspath(spyderpath)):
#            full, short, branch = vcs.get_hg_revision(osp.dirname(spyderpath))
#            if full:
#                revlink = " (%s:r%s)" % (short, full)
#        issue_template = """\
#Spyder Version:  %s%s
#Python Version:  %s
#Qt Version:      %s, %s %s on %s
#
#What steps will reproduce the problem?
#1.
#2.
#3.
#
#What is the expected output? What do you see instead?
#
#
#Please provide any additional information below.
#""" % (__version__,
#       revlink,
#       platform.python_version(),
#       src.gui.qt.QtCore.__version__,
#       src.gui.qt.API_NAME,
#       src.gui.qt.__version__,
#       platform.system())
#       
#        url = QUrl("http://code.google.com/p/spyderlib/issues/entry")
#        url.addEncodedQueryItem("comment", urllib.quote(issue_template))
#        QDesktopServices.openUrl(url)    

    #---- Global callbacks (called from plugins)
#    def get_current_editor_plugin(self):
#        """Return editor plugin which has focus:
#        console, extconsole, editor, inspector or historylog"""
#        if self.light:
#            return self.extconsole
#        widget = QApplication.focusWidget()
#        from src.gui.spyder_widgets.editor import TextEditBaseWidget
#        from src.gui.spyder_widgets.shell import ShellBaseWidget
#        if not isinstance(widget, (TextEditBaseWidget, ShellBaseWidget)):
#            return
#        for plugin in self.widgetlist:
#            if plugin.isAncestorOf(widget):
#                return plugin
#        else:
#            # External Editor window
#            plugin = widget
#            from src.gui.spyder_widgets.editor import EditorWidget
#            while not isinstance(plugin, EditorWidget):
#                plugin = plugin.parent()
#            return plugin
    
    def find(self):
        """
        Global find callback
        """
        plugin = self.get_current_editor_plugin()
        if plugin is not None:
            plugin.find_widget.show()
            plugin.find_widget.search_text.setFocus()
            return plugin
    
    def find_next(self):
        """Global find next callback"""
        plugin = self.get_current_editor_plugin()
        if plugin is not None:
            plugin.find_widget.find_next()
            
    def find_previous(self):
        """Global find previous callback"""
        plugin = self.get_current_editor_plugin()
        if plugin is not None:
            plugin.find_widget.find_previous()
        
    def replace(self):
        """Global replace callback"""
        plugin = self.find()
        if plugin is not None:
            plugin.find_widget.show_replace()
            
    def global_callback(self):
        """Global callback"""
        widget = QApplication.focusWidget()
        action = self.sender()
        callback = from_qvariant(action.data(), unicode)
#        from src.gui.spyder_widgets.editor import TextEditBaseWidget
#        if isinstance(widget, TextEditBaseWidget):
        getattr(widget, callback)()
        

    def open_file(self, fname):
        """
        Open filename with the appropriate application
        Redirect to the right widget (txt -> editor, spydata -> workspace, ...)
        or open file outside Spyder (if extension is not supported)
        """

        fname = unicode(fname)
        ext = osp.splitext(fname)[1]
        if ext in EDIT_EXT:
            self.editor.load(fname)
#        elif self.variableexplorer is not None and ext in IMPORT_EXT\
#             and ext in ('.spydata', '.mat', '.npy', '.h5'):
#            self.variableexplorer.import_data(fname)
        else:
            fname = file_uri(fname)
            programs.start_file(fname)

    #---- PYTHONPATH management, etc.
    def get_spyder_pythonpath(self):
        """Return Openfisca PYTHONPATH"""
        return self.path+self.project_path
        
    def add_path_to_sys_path(self):
        """Add Openfisca path to sys.path"""
        for path in reversed(self.get_spyder_pythonpath()):
            sys.path.insert(1, path)

    def remove_path_from_sys_path(self):

        """Remove Openfisca path from sys.path"""
        sys_path = sys.path
        while sys_path[1] in self.get_spyder_pythonpath():
            sys_path.pop(1)
        
    def path_manager_callback(self):
        """Spyder path manager"""
        self.remove_path_from_sys_path()
#        project_pathlist = self.projectexplorer.get_pythonpath()
#        dialog = PathManager(self, self.path, project_pathlist, sync=True)
#        self.connect(dialog, SIGNAL('redirect_stdio(bool)'),
#                     self.redirect_internalshell_stdio)
#        dialog.exec_()
        self.add_path_to_sys_path()
        encoding.writelines(self.path, self.openfisca_path) # Saving path
        
    def pythonpath_changed(self):
        """Project Explorer PYTHONPATH contribution has changed"""
        self.remove_path_from_sys_path()
        self.project_path = self.projectexplorer.get_pythonpath()
        self.add_path_to_sys_path()
    
    def win_env(self):
        """Show Windows current user environment variables"""
        self.dialog_manager.show(WinUserEnvDialog(self))
        
    #---- Preferences
    def apply_settings(self):
        """
        Apply settings changed in 'Preferences' dialog box
        """
        qapp = QApplication.instance()
        qapp.setStyle(CONF.get('main', 'windows_style', self.default_style))
        
        default = self.DOCKOPTIONS
        if CONF.get('main', 'vertical_tabs'):
            default = default|QMainWindow.VerticalTabs
        if CONF.get('main', 'animated_docks'):
            default = default|QMainWindow.AnimatedDocks
        self.setDockOptions(default)
        
        for child in self.widgetlist:
            features = child.FEATURES
            if CONF.get('main', 'vertical_dockwidget_titlebars'):
                features = features|QDockWidget.DockWidgetVerticalTitleBar
            child.dockwidget.setFeatures(features)
            child.update_margins()
        
        self.apply_statusbar_settings()
        
    def apply_statusbar_settings(self):
        """Update status bar widgets settings"""
        for widget, name in ((self.mem_status, 'memory_usage'),
                             (self.cpu_status, 'cpu_usage')):
            if widget is not None:
                widget.setVisible(CONF.get('main', '%s/enable' % name))
                widget.set_interval(CONF.get('main', '%s/timeout' % name))
        
    def edit_preferences(self):
        """
        Edit openFisca preferences
        """
        dlg = ConfigDialog(self)
        self.connect(dlg, SIGNAL("size_change(QSize)"),
                     lambda s: self.set_prefs_size(s))
        if self.prefs_dialog_size is not None:
            dlg.resize(self.prefs_dialog_size)
        for PrefPageClass in self.general_prefs:
            widget = PrefPageClass(dlg, main=self)
            widget.initialize()
            dlg.add_page(widget)
        
        for plugin in [self.onlinehelp, self.parameters] + self.survey_plugins + self.test_case_plugins + self.thirdparty_plugins:
            if plugin is not None:
                print plugin
                widget = plugin.create_configwidget(dlg)
                if widget is not None:
                    dlg.add_page(widget)
        if self.prefs_index is not None:
            dlg.set_current_index(self.prefs_index)
        dlg.show()
        dlg.check_all_settings()
        self.connect(dlg.pages_widget, SIGNAL("currentChanged(int)"),
                     self.__preference_page_changed)
        dlg.exec_()
        
    def __preference_page_changed(self, index):
        """
        Preference page index has changed
        """
        self.prefs_index = index
    
    def set_prefs_size(self, size):
        """
        Save preferences dialog size
        """
        self.prefs_dialog_size = size

    #---- Shortcuts
    def register_shortcut(self, qaction_or_qshortcut, context, name,
                          default=NoDefault):
        """
        Register QAction or QShortcut to openFisca main application,
        with shortcut (context, name, default)
        """
        self.shortcut_data.append( (qaction_or_qshortcut,
                                    context, name, default) )
        self.apply_shortcuts()
        
    def apply_shortcuts(self):
        """
        Apply shortcuts settings to all widgets/plugins
        """
        toberemoved = []
        for index, (qobject, context, name,
                    default) in enumerate(self.shortcut_data):
            keyseq = QKeySequence( get_shortcut(context, name, default) )
            try:
                if isinstance(qobject, QAction):
                    qobject.setShortcut(keyseq)
                elif isinstance(qobject, QShortcut):
                    qobject.setKey(keyseq)
            except RuntimeError:
                # Object has been deleted
                toberemoved.append(index)
        for index in sorted(toberemoved, reverse=True):
            self.shortcut_data.pop(index)
        
    #---- Sessions
    def load_session(self, filename=None):
        """Load session"""
        if filename is None:
            filename, _selfilter = getopenfilename(self, _("Open session"),
                        os.getcwdu(), _("Openfisca sessions")+" (*.session.tar)")
            if not filename:
                return
        if self.close():
            self.next_session_name = filename
    
    def save_session(self):
        """
        Save session and quit application
        """
        filename, _selfilter = getsavefilename(self, _("Save session"),
                        os.getcwdu(), _("openFisca sessions")+" (*.session.tar)")
        if filename:
            if self.close():
                self.save_session_name = filename

        
def get_options():
    """
    Convert options into commands
    return commands, message
    """
    import optparse
    parser = optparse.OptionParser(usage="ope,fisca [options]")
    parser.add_option('--session', dest="startup_session", default='',
                      help="Startup session")
    parser.add_option('--defaults', dest="reset_to_defaults",
                      action='store_true', default=False,
                      help="Reset to configuration settings to defaults")
    parser.add_option('--reset', dest="reset_session",
                      action='store_true', default=False,
                      help="Remove all configuration files!")
    parser.add_option('--optimize', dest="optimize",
                      action='store_true', default=False,
                      help="Optimize Openfisca bytecode (this may require "
                           "administrative privileges)")
    parser.add_option('-w', '--workdir', dest="working_directory", default=None,
                      help="Default working directory")
    parser.add_option('-d', '--debug', dest="debug", action='store_true',
                      default=False,
                      help="Debug mode (stds are not redirected)")
    options, _args = parser.parse_args()
    return options


def initialize():
    """Initialize Qt, patching sys.exit and eventually setting up ETS"""
    app = qapplication()
    
    #----Monkey patching PyQt4.QtGui.QApplication
    class FakeQApplication(QApplication):
        """Spyder's fake QApplication"""
        def __init__(self, args):
            self = app  # analysis:ignore
        @staticmethod
        def exec_():
            """Do nothing because the Qt mainloop is already running"""
            pass
    from src.gui.qt import QtGui
    QtGui.QApplication = FakeQApplication
    
    
    #----Monkey patching sys.exit
    def fake_sys_exit(arg=[]):
        pass
    sys.exit = fake_sys_exit
    
    # Removing arguments from sys.argv as in standard Python interpreter
    sys.argv = ['']
    
    # Selecting Qt4 backend for Enthought Tool Suite (if installed)
    try:
        from enthought.etsconfig.api import ETSConfig
        ETSConfig.toolkit = 'qt4'
    except ImportError:
        pass

        
    return app


class Spy(object):
    """
    Inspect Spyder internals
    """
    def __init__(self, app, window):
        self.app = app
        self.window = window

def run_spyder(app, options):
    """
    Create and show Openfisca's main window
    Patch matplotlib for figure integration
    Start QApplication event loop
    """

    # Main window
    main = MainWindow(options)
    try:
        main.setup()
    except BaseException:
#        if main.console is not None:
#            try:
#                main.console.shell.exit_interpreter()
#            except BaseException:
#                pass
        raise
    main.show()
    main.post_visible_setup()
    
    app.exec_()
    return main


def __remove_temp_session():
    if osp.isfile(TEMP_SESSION_PATH):
        os.remove(TEMP_SESSION_PATH)

def main():
    """
    Session manager
    """
    __remove_temp_session()
    
    # **** Collect command line options ****
    # Note regarding Options:
    # It's important to collect options before monkey patching sys.exit,
    # otherwise, optparse won't be able to exit if --help option is passed
    options = get_options()    
    app = initialize()
    if options.reset_session:
        # <!> Remove all configuration files!
        reset_session()
        return
    elif options.reset_to_defaults:
        # Reset openFisca settings to defaults
        CONF.reset_to_defaults(save=True)
        return
    elif options.optimize:
        # Optimize the whole Spyder's source code directory
#        import spyderlib TODO: test
#        programs.run_python_script(module="compileall",
#                                   args=[spyderlib.__path__[0]], p_args=['-O'])
        return

    options.debug = True
    if CONF.get('main', 'crash', False):
        CONF.set('main', 'crash', False)
        QMessageBox.information(None, "openFisca",
            u"openFisca crashed during last session.<br><br>"
            u"If openFisca does not start at all and <u>before submitting a "
            u"bug report</u>, please try to reset settings to defaults by "
            u"running openFisca with the command line option '--reset':<br>"
            u"<span style=\'color: #555555\'><b>python openFisca --reset"
            u"</b></span><br><br>"
            u"<span style=\'color: #ff5555\'><b>Warning:</b></span> "
            u"this command will remove all your openFisca configuration files "
            u"located in '%s').<br><br>"
            u"If restoring the default settings does not help, please take "
            u"the time to search for <a href=\"%s\">known bugs</a> or "
            u"<a href=\"%s\">discussions</a> matching your situation before "
            u"eventually creating a new issue <a href=\"%s\">here</a>. "
            u"Your feedback will always be greatly appreciated."
            u"" % (get_conf_path(), __project_url__,
                   __forum_url__, __project_url__))
        
    next_session_name = options.startup_session
    while isinstance(next_session_name, basestring):
        if next_session_name:
            error_message = load_session(next_session_name)
            if next_session_name == TEMP_SESSION_PATH:
                __remove_temp_session()
            if error_message is None:
                CONF.load_from_ini()
            else:
                print error_message
                QMessageBox.critical(None, "Load session",
                                     u"<b>Unable to load '%s'</b>"
                                     u"<br><br>Error message:<br>%s"
                                      % (osp.basename(next_session_name),
                                         error_message))
        mainwindow = None
        try:
            mainwindow = run_spyder(app, options)
        except BaseException:
            CONF.set('main', 'crash', True)
            import traceback
            traceback.print_exc(file=STDERR)
            traceback.print_exc(file=open('openfisca_crash.log', 'wb'))            
        if mainwindow is None:
            # An exception occured
            return
        next_session_name = mainwindow.next_session_name
        save_session_name = mainwindow.save_session_name
        if next_session_name is not None:
            #-- Loading session
            # Saving current session in a temporary file
            # but only if we are not currently trying to reopen it!
            if next_session_name != TEMP_SESSION_PATH:
                save_session_name = TEMP_SESSION_PATH
        if save_session_name:
            #-- Saving session
            error_message = save_session(save_session_name)
            if error_message is not None:
                QMessageBox.critical(None, "Save session",
                                     u"<b>Unable to save '%s'</b>"
                                     u"<br><br>Error message:<br>%s"
                                       % (osp.basename(save_session_name),
                                          error_message))
    ORIGINAL_SYS_EXIT()

if __name__ == "__main__":
    main()
