# -*- coding:utf-8 -*-
# Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

"""
openFisca, Logiciel libre de simulation du système socio-fiscal français
Copyright © 2011 Clément Schaff, Mahdi Ben Jelloul

This file is part of openFisca.

    openFisca is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    openFisca is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with openFisca.  If not, see <http://www.gnu.org/licenses/>.
"""

import os, os.path as osp

from PyQt4.QtGui import (QWidget, QDialog, QListWidget, QListWidgetItem, QVBoxLayout, 
                         QStackedWidget, QListView, QHBoxLayout, QDialogButtonBox, 
                         QMessageBox, QLabel, QSpinBox, QDoubleSpinBox, QPushButton, 
                         QGroupBox, QComboBox, QDateEdit, QFileDialog, QIcon, QLineEdit,
                         QRadioButton, QButtonGroup)
from PyQt4.QtCore import Qt, QSize, SIGNAL, SLOT, QVariant, QDate
from ConfigParser import RawConfigParser
from datetime import datetime
VERSION = "0.1.4"

class NoDefault:
    pass


DEFAULTS = [
            ('simulation', 
             {
              'country': 'france',
              'datesim': '2006-01-01',
#              'survey_year': '2006-01-01',
              'nmen': 101,
              'xaxis':  'sal',
              'maxrev': 50000,
              }),
            ('paths',
             {'data_dir': 'france/data',
              'cas_type_dir': 'france/castypes',
              'reformes_dir': 'france/reformes',
              'calib_dir'   :  'france/calibrations',
              'survey_data/file':'france/data/survey.h5',
              'survey_data/bareme_only': False,
              'survey_data/survey_enabled': True,
              'output_dir' : os.path.expanduser('~'),
              'table': 'csv',
# TODO:              'image': '',
              }),
            ('calibration', 
             {'inputs_filename': 'calage_men.csv',
              'pfam_filename': 'calage_pfam.csv',
              'method': 'logit',
              'up': 3.0,
              'invlo': 3.0,
              })
            ]

class UserConfigParser(RawConfigParser):
    def __init__(self, defaults, filename):
        RawConfigParser.__init__(self)
        self.defaults = defaults

        try:
            open(filename)
            self.read(filename)
        except:
            for section in DEFAULTS:
                self.add_section(section[0])
                for key, val in section[1].iteritems():
                    self.set(section[0], key, val)

    def get(self, section, option):
#    def get(self, section, option, default=NoDefault):
        """
        Get an option
        section=None: attribute a default section name
        default: default value (if not specified, an exception
        will be raised if option doesn't exist)
        """
#        section = self.__check_section_option(section, option)
#
#        if not self.has_section(section):
#            if default is NoDefault:
#                raise NoSectionError(section)
#            else:
#                self.add_section(section)
#        
#        if not self.has_option(section, option):
#            if default is NoDefault:
#                raise NoOptionError(option, section)
#            else:
#                self.set(section, option, default)
#                return default
            
#        value = ConfigParser.get(self, section, option, self.raw)
        value = RawConfigParser.get(self, section, option)
        default_value = self.get_default(section, option)
        if isinstance(default_value, bool):
            if not isinstance(value, bool):
                value = eval(value)
        elif isinstance(default_value, float):
            value = float(value)
        elif isinstance(default_value, int):
            value = int(value)
        else:
            try:
                value = datetime.strptime(value ,"%Y-%m-%d").date()
            except:
                pass
                
#        else:
#            if isinstance(default_value, basestring):
#                try:
#                    value = value.decode('utf-8')
#                except (UnicodeEncodeError, UnicodeDecodeError):
#                    pass
#            try:
#                # lists, tuples, ...
#                value = eval(value)
#                print value
#            except:
#                pass
        return value

    def get_default(self, section, option):
        """
        Get Default value for a given (section, option)
        -> useful for type checking in 'get' method
        """
#        section = self.__check_section_option(section, option)
        for sec, options in self.defaults:
            if sec == section:
                if option in options:
                    return options[ option ]
#        else:
#            return NoDefault

CONF = UserConfigParser(DEFAULTS, 'main.cfg')

def get_icon(iconFile):
    return QIcon()

def get_std_icon(iconFile):
    return QIcon()

class ConfigPage(QWidget):
    """Configuration page base class"""
    def __init__(self, parent, apply_callback=None):
        QWidget.__init__(self, parent)
        self.apply_callback = apply_callback
        self.is_modified = False
        
    def initialize(self):
        """
        Initialize configuration page:
            * setup GUI widgets
            * load settings and change widgets accordingly
        """
        self.setup_page()
        self.load_from_conf()
        
    def get_name(self):
        """Return page name"""
        raise NotImplementedError
    
    def get_icon(self):
        """Return page icon"""
        raise NotImplementedError
    
    def setup_page(self):
        """Setup configuration page widget"""
        raise NotImplementedError
        
    def set_modified(self, state):
        self.is_modified = state
        self.emit(SIGNAL("apply_button_enabled(bool)"), state)
        
    def is_valid(self):
        """Return True if all widget contents are valid"""
        raise NotImplementedError
    
    def apply_changes(self):
        """Apply changes callback"""
        if self.is_modified:
            self.save_to_conf()
            if self.apply_callback is not None:
                self.apply_callback()
            self.set_modified(False)
    
    def load_from_conf(self):
        """Load settings from configuration file"""
        raise NotImplementedError
    
    def save_to_conf(self):
        """Save settings to configuration file"""
        raise NotImplementedError


class ConfigDialog(QDialog):
    def __init__(self, parent=None):
        QDialog.__init__(self, parent)

        self.contents_widget = QListWidget()
        self.contents_widget.setMovement(QListView.Static)
        self.contents_widget.setMinimumWidth(120)
        self.contents_widget.setMaximumWidth(120)
        self.contents_widget.setSpacing(1)

        bbox = QDialogButtonBox(QDialogButtonBox.Ok|QDialogButtonBox.Apply
                                     |QDialogButtonBox.Cancel)
        self.apply_btn = bbox.button(QDialogButtonBox.Apply)
        self.connect(bbox, SIGNAL("accepted()"), SLOT("accept()"))
        self.connect(bbox, SIGNAL("rejected()"), SLOT("reject()"))
        self.connect(bbox, SIGNAL("clicked(QAbstractButton*)"),
                     self.button_clicked)

        self.pages_widget = QStackedWidget()
        self.connect(self.pages_widget, SIGNAL("currentChanged(int)"),
                     self.current_page_changed)

        self.connect(self.contents_widget, SIGNAL("currentRowChanged(int)"),
                     self.pages_widget.setCurrentIndex)
        self.contents_widget.setCurrentRow(0)

        hlayout = QHBoxLayout()
        hlayout.addWidget(self.contents_widget)
        hlayout.addWidget(self.pages_widget)
        hlayout.setStretch(1,1)

        btnlayout = QHBoxLayout()
        btnlayout.addStretch(1)
        btnlayout.addWidget(bbox)

        vlayout = QVBoxLayout()
        vlayout.addLayout(hlayout)
        vlayout.addLayout(btnlayout)

        self.setLayout(vlayout)

        self.setWindowTitle("Preferences")
        self.setWindowIcon(get_icon("configure.png"))
        
    def get_current_index(self):
        """Return current page index"""
        return self.contents_widget.currentRow()
        
    def set_current_index(self, index):
        """Set current page index"""
        self.contents_widget.setCurrentRow(index)
        
    def accept(self):
        """Reimplement Qt method"""
        for index in range(self.pages_widget.count()):
            configpage = self.pages_widget.widget(index)
            if not configpage.is_valid():
                return
            configpage.apply_changes()
        QDialog.accept(self)
        
    def button_clicked(self, button):
        if button is self.apply_btn:
            # Apply button was clicked
            configpage = self.pages_widget.currentWidget()
            if not configpage.is_valid():
                return
            configpage.apply_changes()
            
    def current_page_changed(self, index):
        widget = self.pages_widget.widget(index)
        self.apply_btn.setVisible(widget.apply_callback is not None)
        self.apply_btn.setEnabled(widget.is_modified)
        
    def add_page(self, widget):
        self.connect(self, SIGNAL('check_settings()'), widget.check_settings)
        self.connect(widget, SIGNAL('show_this_page()'),
                     lambda row=self.contents_widget.count():
                     self.contents_widget.setCurrentRow(row))
        self.connect(widget, SIGNAL("apply_button_enabled(bool)"),
                     self.apply_btn.setEnabled)
        self.pages_widget.addWidget(widget)
        item = QListWidgetItem(self.contents_widget)
        item.setIcon(widget.get_icon())
        item.setText(widget.get_name())
        item.setFlags(Qt.ItemIsSelectable|Qt.ItemIsEnabled)
        item.setSizeHint(QSize(0, 25))
        
    def check_all_settings(self):
        """This method is called to check all configuration page settings
        after configuration dialog has been shown"""
        self.emit(SIGNAL('check_settings()'))


class OpenFiscaConfigPage(ConfigPage):
    """Plugin configuration dialog box page widget"""
    def __init__(self, parent):
        ConfigPage.__init__(self, parent,
                            apply_callback=lambda:
                            self.apply_settings(self.changed_options))
        self.checkboxes = {}
        self.radiobuttons = {}
        self.lineedits = {}
        self.validate_data = {}
        self.spinboxes = {}
        self.dateedits = {}
        self.comboboxes = {}
        self.changed_options = set()
        self.default_button_group = None
        
    def apply_settings(self, options):
        raise NotImplementedError
    
    def check_settings(self):
        """This method is called to check settings after configuration 
        dialog has been shown"""
        pass
        
    def set_modified(self, state):
        ConfigPage.set_modified(self, state)
        if not state:
            self.changed_options = set()
        
    def is_valid(self):
        """Return True if all widget contents are valid"""
        for lineedit in self.lineedits:
            if lineedit in self.validate_data and lineedit.isEnabled():
                validator, invalid_msg = self.validate_data[lineedit]
                text = unicode(lineedit.text())
                if not validator(text):
                    QMessageBox.critical(self, self.get_name(),
                                     "%s:<br><b>%s</b>" % (invalid_msg, text),
                                     QMessageBox.Ok)
                    return False
        return True
        
    def load_from_conf(self):
        """Load settings from configuration file"""
        for checkbox, option in self.checkboxes.items():
            checkbox.setChecked(self.get_option(option))
            checkbox.setProperty("option", QVariant(option))
            self.connect(checkbox, SIGNAL("clicked(bool)"),
                         lambda checked: self.has_been_modified())

        for radiobutton, option in self.radiobuttons.items():
            radiobutton.setChecked(self.get_option(option))
            radiobutton.setProperty("option", QVariant(option))
            self.connect(radiobutton, SIGNAL("toggled(bool)"),
                         lambda checked: self.has_been_modified())

        for lineedit, option in self.lineedits.items():
            lineedit.setText(self.get_option(option))
            lineedit.setProperty("option", QVariant(option))
            self.connect(lineedit, SIGNAL("textChanged(QString)"),
                         lambda text: self.has_been_modified())

        for spinbox, option in self.spinboxes.items():
            spinbox.setValue(self.get_option(option))
            spinbox.setProperty("option", QVariant(option))
            self.connect(spinbox, SIGNAL('valueChanged(int)'),
                         lambda value: self.has_been_modified())
            
        for dateedit, option in self.dateedits.items():
            dateedit.setDate(self.get_option(option))
            dateedit.setProperty("option", QVariant(option))
            self.connect(dateedit, SIGNAL('dateChanged(QDate)'),
                         lambda value: self.has_been_modified())
            
        for combobox, option in self.comboboxes.items():
            value = self.get_option(option)
            for index in range(combobox.count()):
                if unicode(combobox.itemData(index).toString()
                           ) == unicode(value):
                    break
            combobox.setCurrentIndex(index)
            combobox.setProperty("option", QVariant(option))
            self.connect(combobox, SIGNAL('currentIndexChanged(int)'),
                         lambda index: self.has_been_modified())


    def save_to_conf(self):
        """Save settings to configuration file"""
        for checkbox, option in self.checkboxes.items():
            self.set_option(option, checkbox.isChecked())
        for radiobutton, option in self.radiobuttons.items():
            self.set_option(option, radiobutton.isChecked())
        for lineedit, option in self.lineedits.items():
            self.set_option(option, unicode(lineedit.text()))
        for spinbox, option in self.spinboxes.items():
            self.set_option(option, spinbox.value())
        for dateedit, option in self.dateedits.items():
            self.set_option(option, str(dateedit.date().toString(Qt.ISODate)))
        for combobox, option in self.comboboxes.items():
            data = combobox.itemData(combobox.currentIndex())
            self.set_option(option, unicode(data.toString()))
        with open('main.cfg', 'wb') as configfile:
            CONF.write(configfile)

    def has_been_modified(self):
        option = unicode(self.sender().property("option").toString())
        self.set_modified(True)
        self.changed_options.add(option)
    
    def create_lineedit(self, text, option, 
                        tip=None, alignment=Qt.Vertical):
        label = QLabel(text)
        label.setWordWrap(True)
        edit = QLineEdit()
        layout = QVBoxLayout() if alignment == Qt.Vertical else QHBoxLayout()
        layout.addWidget(label)
        layout.addWidget(edit)
        layout.setContentsMargins(0, 0, 0, 0)
        if tip:
            edit.setToolTip(tip)
        self.lineedits[edit] = option
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget
    
    def create_browsedir(self, text, option, tip=None):
        widget = self.create_lineedit(text, option,
                                      alignment=Qt.Horizontal)
        for edit in self.lineedits:
            if widget.isAncestorOf(edit):
                break
        msg = "Invalid directory path"
        self.validate_data[edit] = (osp.isdir, msg)
        browse_btn = QPushButton(get_std_icon('DirOpenIcon'), "", self)
        browse_btn.setToolTip("Select directory")
        self.connect(browse_btn, SIGNAL("clicked()"),
                     lambda: self.select_directory(edit))
        layout = QHBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(browse_btn)
        layout.setContentsMargins(0, 0, 0, 0)
        browsedir = QWidget(self)
        browsedir.setLayout(layout)
        return browsedir

    def select_directory(self, edit):
        """Select directory"""
        basedir = unicode(edit.text())
        if not osp.isdir(basedir):
            basedir = os.getcwdu()
        title = "Select directory"
        directory = QFileDialog.getExistingDirectory(self, title, basedir)
        if not directory.isEmpty():
            edit.setText(directory)
    
    def create_browsefile(self, text, option, tip=None, filters=None):
        widget = self.create_lineedit(text, option, alignment=Qt.Horizontal)
        for edit in self.lineedits:
            if widget.isAncestorOf(edit):
                break
        msg = "Invalid file path"
        self.validate_data[edit] = (osp.isfile, msg)
        browse_btn = QPushButton(get_std_icon('FileIcon'), "", self)
        browse_btn.setToolTip("Selectionner un fichier")
        self.connect(browse_btn, SIGNAL("clicked()"),
                     lambda: self.select_file(edit, filters))
        layout = QHBoxLayout()
        layout.addWidget(widget)
        layout.addWidget(browse_btn)
        layout.setContentsMargins(0, 0, 0, 0)
        browsedir = QWidget(self)
        browsedir.setLayout(layout)
        return browsedir

    def select_file(self, edit, filters=None):
        """Select File"""
        basedir = osp.dirname(unicode(edit.text()))
        if not osp.isdir(basedir):
            basedir = os.getcwdu()
        if filters is None:
            filters = "All files (*)"
        title = "Select file"
        filename = QFileDialog.getOpenFileName(self, title, basedir, filters)
        if filename:
            edit.setText(filename)
    
    def create_spinbox(self, prefix, suffix, option, 
                       min_=None, max_=None, step=None, tip=None):
        if prefix:
            plabel = QLabel(prefix)
        else:
            plabel = None
        if suffix:
            slabel = QLabel(suffix)
        else:
            slabel = None
        spinbox = QSpinBox()
        if min_ is not None:
            spinbox.setMinimum(min_)
        if max_ is not None:
            spinbox.setMaximum(max_)
        if step is not None:
            spinbox.setSingleStep(step)
        if tip is not None:
            spinbox.setToolTip(tip)
        self.spinboxes[spinbox] = option
        layout = QHBoxLayout()
        for subwidget in (plabel, spinbox, slabel):
            if subwidget is not None:
                layout.addWidget(subwidget)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.setLayout(layout)
        widget.spin = spinbox
        return widget

    def create_doublespinbox(self, prefix, suffix, option, 
                       min_=None, max_=None, step=None, tip=None):
        if prefix:
            plabel = QLabel(prefix)
        else:
            plabel = None
        if suffix:
            slabel = QLabel(suffix)
        else:
            slabel = None
        spinbox = QDoubleSpinBox()
        if min_ is not None:
            spinbox.setMinimum(min_)
        if max_ is not None:
            spinbox.setMaximum(max_)
        if step is not None:
            spinbox.setSingleStep(step)
        if tip is not None:
            spinbox.setToolTip(tip)
        self.spinboxes[spinbox] = option
        layout = QHBoxLayout()
        for subwidget in (plabel, spinbox, slabel):
            if subwidget is not None:
                layout.addWidget(subwidget)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.setLayout(layout)
        widget.spin = spinbox
        return widget
        
    def create_dateedit(self, text, option, tip=None, min_date = None, max_date = None):
        label = QLabel(text)
        dateedit = QDateEdit()
        dateedit.setDisplayFormat('dd MMM yyyy')
        if min_date: dateedit.setMinimumDate(min_date)
        if max_date: dateedit.setMaximumDate(max_date)
        if tip: dateedit.setToolTip(tip)
        self.dateedits[dateedit] = option
        layout = QHBoxLayout()
        for subwidget in (label, dateedit):
            layout.addWidget(subwidget)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.setLayout(layout)
        return widget
    
    def create_combobox(self, text, choices, option, tip=None):
        """choices: couples (name, key)"""
        label = QLabel(text)
        combobox = QComboBox()
        if tip is not None:
            combobox.setToolTip(tip)
        for name, key in choices:
            combobox.addItem(name, QVariant(key))
        self.comboboxes[combobox] = option
        layout = QHBoxLayout()
        for subwidget in (label, combobox):
            layout.addWidget(subwidget)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        widget = QWidget(self)
        widget.setLayout(layout)
        widget.box = combobox
        return widget    

    def create_radiobutton(self, text, option, default=NoDefault,
                           tip=None, msg_warning=None, msg_info=None,
                           msg_if_enabled=False, button_group=None):
        radiobutton = QRadioButton(text)
        if button_group is None:
            if self.default_button_group is None:
                self.default_button_group = QButtonGroup(self)
            button_group = self.default_button_group
        button_group.addButton(radiobutton)
        if tip is not None:
            radiobutton.setToolTip(tip)
        self.radiobuttons[radiobutton] = option
        if msg_warning is not None or msg_info is not None:
            def show_message(is_checked):
                if is_checked or not msg_if_enabled:
                    if msg_warning is not None:
                        QMessageBox.warning(self, self.get_name(),
                                            msg_warning, QMessageBox.Ok)
                    if msg_info is not None:
                        QMessageBox.information(self, self.get_name(),
                                                msg_info, QMessageBox.Ok)
            self.connect(radiobutton, SIGNAL("toggled(bool)"), show_message)
        return radiobutton


class GeneralConfigPage(OpenFiscaConfigPage):
    CONF_SECTION = None
    def __init__(self, parent, main):
        OpenFiscaConfigPage.__init__(self, parent)
        self.main = main

    def set_option(self, option, value):
        CONF.set(self.CONF_SECTION, option, value)

    def get_option(self, option):
        return CONF.get(self.CONF_SECTION, option)
            
    def apply_settings(self, options):
        raise NotImplementedError

class SimConfigPage(GeneralConfigPage):
    CONF_SECTION = "simulation"
    def get_name(self):
        return "Simulation"
    
    def get_icon(self):
        return get_icon("simprefs.png")
    
    def setup_page(self):        
        simulation_group = QGroupBox("Simulation")
        
        country_choices = [(u'France', 'france'),(u'Tunisie', 'tunisia')]
        country_combo = self.create_combobox('Pays', country_choices, 'country')
        sim_dateedit = self.create_dateedit("Date de la simulation", 'datesim', min_date = QDate(2002,01,01), max_date = QDate(2012,12,31))
        nmen_spinbox = self.create_spinbox(u'Nombre de ménages', '', 'nmen', min_ = 1, max_ = 10001, step = 100)
        xaxis_choices = [(u'Salaires', 'sal'),(u'Chômage', 'cho'), (u'Retraites', 'rst')]
        xaxis_combo = self.create_combobox('Axe des abscisses', xaxis_choices, 'xaxis')
        maxrev_spinbox = self.create_spinbox("Revenu maximum", 
                                             'euros', 'maxrev', min_ = 0, max_ = 10000000, step = 1000)
        
        simulation_layout = QVBoxLayout()
        simulation_layout.addWidget(country_combo)
        simulation_layout.addWidget(sim_dateedit)
        simulation_layout.addWidget(nmen_spinbox)
        simulation_layout.addWidget(xaxis_combo)
        simulation_layout.addWidget(maxrev_spinbox)

        simulation_group.setLayout(simulation_layout)
        
        vlayout = QVBoxLayout()
        vlayout.addWidget(simulation_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)
        
    def apply_settings(self, options):
        self.main.apply_settings()
        
class CalConfigPage(GeneralConfigPage):
    CONF_SECTION = "calibration"
    def get_name(self):
        return "Calibration"
    
    def get_icon(self):
        return get_icon("simprefs.png")
    
    def setup_page(self):        
        calibration_group = QGroupBox("Calibration")
        
        # TODO cal_dateedit = self.create_dateedit("Date des paramètres de la calibration", 'datecal')
                
        method_choices = [(u'Linéaire', 'linear'),(u'Raking ratio', 'raking ratio'), (u'Logit', 'logit')]
        method_combo = self.create_combobox(u'Méthode par défaut', method_choices, 'method')
        up_spinbox = self.create_spinbox(u'Ratio de poids maximal autorisé', '', 'up', min_ = 1   , max_ = 100, step = 1)    
        invlo_spinbox = self.create_spinbox(u'Ratio de poids minimal autorisé', '', 'invlo', min_ = 1, max_ = 100, step = 1)
        # calib_file_edit = self.create_browsefile(u'Emplacement des données de calibration', 'filename', tip=None, filters='*.csv')       
        
        calibration_layout = QVBoxLayout()
        calibration_layout.addWidget(method_combo)
        calibration_layout.addWidget(up_spinbox)
        calibration_layout.addWidget(invlo_spinbox)
#        calibration_layout.addWidget(calib_file_edit)

        calibration_group.setLayout(calibration_layout)
        
        vlayout = QVBoxLayout()
        vlayout.addWidget(calibration_group)
        vlayout.addStretch(1)
        self.setLayout(vlayout)
        
    def apply_settings(self, options):
        self.main.apply_settings()






class PathConfigPage(GeneralConfigPage):
    CONF_SECTION = "paths"
    def get_name(self):
        return "Chemins"
    
    def get_icon(self):
        return get_icon("cheminprefs.png")
    
    def setup_page(self):
        
        dirs_group = QGroupBox(u"Répertoires de sauvegarde")
        cas_type_dir = self.create_browsedir(u'Cas types', 'cas_type_dir')
        reformes_dir = self.create_browsedir(u'Réformes', 'reformes_dir')
        calib_dir = self.create_browsedir(u'Calages', 'calib_dir')
        data_dir = self.create_browsedir(u'Données internes', 'data_dir')
        
        
        survey_group = QGroupBox(u"Données d'enquête")
        survey_bg = QButtonGroup(self)
        survey_label = QLabel(u"Emplacement des données d'enquête pour la microsimulation")

        bareme_only_radio = self.create_radiobutton(u"Mode barème uniquement",
                                                    'survey_data/bareme_only', False,
                                                    u"Mode barème uniquement",
                                button_group = survey_bg)
        survey_radio = self.create_radiobutton("le fichier suivant",
                                               'survey_data/survey_enabled', True,
                                               "Fichier de données pour la microsimulation",
                                               button_group=survey_bg)
        survey_file = self.create_browsefile("", 'survey_data/file',
                                             filters='*.h5')
        
        
        self.connect(bareme_only_radio, SIGNAL("toggled(bool)"),
                     survey_file.setDisabled)
        self.connect(survey_radio, SIGNAL("toggled(bool)"),
                     survey_file.setEnabled)
        survey_file_layout = QHBoxLayout()
        survey_file_layout.addWidget(survey_radio)
        survey_file_layout.addWidget(survey_file)

        survey_layout = QVBoxLayout()
        survey_layout.addWidget(survey_label)
        survey_layout.addWidget(bareme_only_radio)
        survey_layout.addLayout(survey_file_layout)
        survey_group.setLayout(survey_layout)

        dirs_layout = QVBoxLayout()
        dirs_layout.addWidget(cas_type_dir)
        dirs_layout.addWidget(reformes_dir)
        dirs_layout.addWidget(calib_dir)
        dirs_group.setLayout(dirs_layout)

        # Formats
        format_group = QGroupBox(u"Formats")
        table_format_choices = [(u".csv", 'csv'), (u".xls", 'xls')]
        table_format = self.create_combobox("Format d'exportation des tableaux", table_format_choices, 'table')
        
        format_layout = QVBoxLayout() 
        format_layout.addWidget(table_format)
        format_group.setLayout(format_layout)
        
        paths_layout = QVBoxLayout()
        paths_layout.addWidget(dirs_group)
        paths_layout.addWidget(survey_group)
        paths_layout.addWidget(format_group)
        paths_layout.addWidget(data_dir)
        
        paths_layout.addStretch(1)
        self.setLayout(paths_layout)

    def apply_settings(self, options):
        self.main.enable_aggregate(True)

def test():
    import sys
    from PyQt4.QtGui import QApplication
    app = QApplication(sys.argv)
    dlg = ConfigDialog()
    for ConfigPage in [CalConfigPage]: # 
        widget = ConfigPage(dlg, main=None)
        widget.initialize()
        dlg.add_page(widget)

    dlg.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test()
    