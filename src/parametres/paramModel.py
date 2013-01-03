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

from src.qt.QtGui import QColor
from src.qt.QtCore import QAbstractItemModel, Qt, QModelIndex
from src.qt.compat import to_qvariant

class PrestationModel(QAbstractItemModel):
    def __init__(self, root, parent=None):
        super(PrestationModel, self).__init__(parent)
        self._rootNode = root

    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self._rootNode
        else:
            parentNode = self.getNode(parent)

        return parentNode.childCount()

    def columnCount(self, parent):
        return 3
    
    def data(self, index, role = Qt.DisplayRole):        
        if not index.isValid():
            return None

        node = self.getNode(index)

        if role == Qt.DisplayRole or role == Qt.EditRole:
            return to_qvariant(node.data(index.column()))
        if role == Qt.ToolTipRole:
            return node.code
        # warning this role is deprecated, use foregroundrole instead
        if role == Qt.TextColorRole: 
            if node.isDirty(): return QColor(Qt.red)
            else: return QColor(Qt.black)
     
    def setData(self, index, value, role = Qt.EditRole):
        if not index.isValid():
            return None
        node = self.getNode(index)
        column = index.column()
        if role == Qt.EditRole:
            node.setData(column, value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if   section == 0: return u"Prestation"
            elif section == 1: return u"Défaut"
            elif section == 2: return u"Valeur"
        if role == Qt.TextAlignmentRole:
            if section == 0: return Qt.AlignLeft
            else: return Qt.AlignRight
    
    def flags(self, index):
        col = index.column()
        node = self.getNode(index)
        if col == 0:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
        elif col == 1:
            return Qt.ItemIsSelectable 
        elif col == 2:
            if node.typeInfo == 'NODE':
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable 
            else:
                return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable

    """Should return the parent of the node with the given QModelIndex"""
    def parent(self, index):        
        node = self.getNode(index)
        parentNode = node.parent()        
        if parentNode == self._rootNode:
            return QModelIndex()
        
        return self.createIndex(parentNode.row(), 0, parentNode)
        
    """Should return a QModelIndex that corresponds to the given row, column and parent node"""
    def index(self, row, column, parent):
        parentNode = self.getNode(parent)
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QModelIndex()

    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node            
        return self._rootNode
