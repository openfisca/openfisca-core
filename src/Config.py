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

from PyQt4.QtGui import (QWidget, QDialog, QListWidget, QListWidgetItem,
                                QVBoxLayout, QStackedWidget, QListView,
                                QHBoxLayout, QDialogButtonBox,QMessageBox, 
                                QLabel, QSpinBox, QPushButton, QGroupBox, 
                                QComboBox, QDateEdit, QFileDialog,
                                QSplitter, QIcon, QLineEdit)
from PyQt4.QtCore import Qt, QSize, SIGNAL, SLOT, QVariant, QDate
from ConfigParser import RawConfigParser

VERSION = "0.1.0"

DEFAULTS = [
            ('simulation', 
             {
              'datesim': '2010-01-01',
              'nmen': 101,
              'xaxis':  'sal',
              'maxrev': 50000,
              }),
            ('paths',
             {'external_data_file':'C:/Users/Utilisateur/Documents/Data/R/erf/2006/final.csv',
              'data_dir': 'data',
              'cas_type_dir': 'castypes',
              'reformes_dir': 'reformes',
              'output_dir' : os.path.expanduser('~'),
              })]

class UserConfigParser(RawConfigParser):
    def __init__(self, defaults):
        RawConfigParser.__init__(self)
        for section in DEFAULTS:
            self.add_section(section[0])
            for key, val in section[1].iteritems():
                self.set(section[0], key, val)
        
CONF = UserConfigParser(DEFAULTS)

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
        self.contents_widget.setMinimumWidth(160 if os.name == 'nt' else 200)
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

        hsplitter = QSplitter()
        hsplitter.addWidget(self.contents_widget)
        hsplitter.addWidget(self.pages_widget)

        btnlayout = QHBoxLayout()
        btnlayout.addStretch(1)
        btnlayout.addWidget(bbox)

        vlayout = QVBoxLayout()
        vlayout.addWidget(hsplitter)
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
            dateedit.setDate(QDate.fromString(self.get_option(option), Qt.ISODate))
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
        browse_btn.setToolTip("Select file")
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
        
    def create_dateedit(self, text, option, tip=None):
        label = QLabel(text)
        dateedit = QDateEdit()
        dateedit.setDisplayFormat('dd MMM yyyy')
        dateedit.setMaximumDate(QDate(2010,12,31))
        dateedit.setMinimumDate(QDate(2002,01,01))
        if tip is not None: dateedit.setToolTip(tip)
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
        sim_dateedit = self.create_dateedit("Date de la simulation", 'datesim')
        nmen_spinbox = self.create_spinbox(u'Nombre de ménages', '', 'nmen', min_ = 1, max_ = 10001, step = 100)
        xaxis_choices = [(u'Salaires', 'sal'),(u'Chômage', 'cho'), (u'Retraites', 'rst')]
        xaxis_combo = self.create_combobox('Axe des abscisses', xaxis_choices, 'xaxis')
        maxrev_spinbox = self.create_spinbox("Revenu maximum", 
                                             'euros', 'maxrev', min_ = 0, max_ = 10000000, step = 1000)
        
        simulation_layout = QVBoxLayout()
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

class PathConfigPage(GeneralConfigPage):
    CONF_SECTION = "paths"
    def get_name(self):
        return "Chemins"
    
    def get_icon(self):
        return get_icon("cheminprefs.png")
    
    def setup_page(self):
        cas_type_dir = self.create_browsedir(u'Emplacement des cas types', 'cas_type_dir')
        reformes_dir = self.create_browsedir(u'Emplacement des réformes', 'reformes_dir')
        external_data_file_edit = self.create_browsefile(u'Emplacement des données externes', 'external_data_file', tip=None, filters='*.csv')
        data_dir = self.create_browsedir(u'Emplacement des données internes', 'data_dir')
        paths_layout = QVBoxLayout()
        paths_layout.addWidget(cas_type_dir)
        paths_layout.addWidget(reformes_dir)
        paths_layout.addWidget(external_data_file_edit)
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
    for ConfigPage in [SimConfigPage]: # 
        widget = ConfigPage(dlg, main=None)
        widget.initialize()
        dlg.add_page(widget)

    dlg.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test()
    