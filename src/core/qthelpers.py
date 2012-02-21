# -*- coding:utf-8 -*-
# Copyright © 2012 Clément Schaff, Mahdi Ben Jelloul

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

from PyQt4.QtGui import QAction, QMenu, QIcon, QTreeView, QTableView, QApplication, QPixmap, QIcon
from PyQt4.QtCore import Qt, SIGNAL, QVariant, QString

def toggle_actions(actions, enable):
    """Enable/disable actions"""
    if actions is not None:
        for action in actions:
            if action is not None:
                action.setEnabled(enable)

def create_action(parent, text, shortcut=None, icon=None, tip=None,
                  toggled=None, triggered=None, data=None,
                  context=Qt.WindowShortcut):
    """Create a QAction"""
    action = QAction(text, parent)
    if triggered is not None:
        parent.connect(action, SIGNAL("triggered()"), triggered)
    if toggled is not None:
        parent.connect(action, SIGNAL("toggled(bool)"), toggled)
        action.setCheckable(True)
    if icon is not None:
        if isinstance(icon, (str, unicode)):
            icon = get_icon(icon)
        action.setIcon( icon )
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if data is not None:
        action.setData(QVariant(data))
    #TODO: Hard-code all shortcuts and choose context=Qt.WidgetShortcut
    # (this will avoid calling shortcuts from another dockwidget
    #  since the context thing doesn't work quite well with these widgets)
    action.setShortcutContext(context)
    return action

def add_actions(target, actions, insert_before=None):
    """Add actions to a menu"""
    previous_action = None
    target_actions = list(target.actions())
    if target_actions:
        previous_action = target_actions[-1]
        if previous_action.isSeparator():
            previous_action = None
    for action in actions:
        if (action is None) and (previous_action is not None):
            if insert_before is None:
                target.addSeparator()
            else:
                target.insertSeparator(insert_before)
        elif isinstance(action, QMenu):
            if insert_before is None:
                target.addMenu(action)
            else:
                target.insertMenu(insert_before, action)
        elif isinstance(action, QAction):
            if insert_before is None:
                target.addAction(action)
            else:
                target.insertAction(insert_before, action)
        previous_action = action

def get_icon(name):
    """Return image inside a QIcon object"""
    image_path = ":/images/" + name
    icon = QIcon()
    icon.addPixmap(QPixmap(image_path), QIcon.Normal, QIcon.Off)
    return icon

class OfTreeView(QTreeView):
    def __init__(self, parent = None):
        super(OfTreeView, self).__init__(parent)
        
    def copy(self):
        '''
        Copy the table selection to the clipboard
        At this point, works only for single line selection
        '''
        selection = self.selectionModel()
        indexes = selection.selectedIndexes();
        selected_text = QString()        
        for current in indexes:
            data = self.model().data(current)
            text = data.toString()
            selected_text.append(text + '\t')
        QApplication.clipboard().setText(selected_text);

class OfTableView(QTableView):
    def __init__(self, parent = None):
        super(OfTableView, self).__init__(parent)
        
    def copy(self):
        '''
        Copy the table selection to the clipboard
        '''
        selection = self.selectionModel()
        indexes = selection.selectedIndexes();
        previous = indexes.pop(0)
        data = self.model().data(previous)
        text = data.toString()
        selected_text = QString(text)
        for current in indexes:
            if current.row() != previous.row():
                selected_text.append('\n')
            else:
                selected_text.append('\t')
            data = self.model().data(current)
            text = data.toString()
            selected_text.append(text)
        QApplication.clipboard().setText(selected_text);
