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

from PyQt4.QtGui import (QAction, QMenu, QTreeView, QTableView, QApplication, QPixmap, QIcon,
                         QWidget, QLabel, QHBoxLayout, QComboBox, QSpinBox, QDoubleSpinBox)


from PyQt4.QtCore import Qt, SIGNAL, QVariant, QString, QAbstractTableModel
from pandas import DataFrame
from numpy import isnan, isinf

try:
    _fromUtf8 = QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s



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
    """
    Add actions to a menu
    """
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
    """
    Return image inside a QIcon object
    """
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
        indexes = selection.selectedIndexes()
        indexes.sort()

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
            previous = current
        selected_text.append('\n')
        QApplication.clipboard().setText(selected_text)

class DataFrameViewWidget(QTableView):
    '''
    a conveniance widget to see a dataframe in a QTableView
    '''
    def __init__(self, parent = None):
        super(DataFrameViewWidget, self).__init__(parent)
        self.roles = {}

    def set_dataframe(self, dataframe):
        model = DataFrameModel(dataframe, self)
        self.setModel(model)

    def clear(self):
        model = self.model()
        if model:
            model.clear()
        self.reset()
        
    def copy(self):
        '''
        Copy the table selection to the clipboard
        '''
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()
        indexes.sort()
        previous = indexes.pop(0)
        data = self.model().data(previous)
        try:
            text = data.toString()
        except:
            text = str(data)
        selected_text = QString(text)

        for current in indexes:
            if current.row() != previous.row():
                selected_text.append('\n')
            else:
                selected_text.append('\t')
            data = self.model().data(current)
            try:
                text = data.toString()
            except:
                text = str(data)
            selected_text.append(text)
            previous = current
        selected_text.append('\n')
        QApplication.clipboard().setText(selected_text)


class DataFrameModel(QAbstractTableModel):
    def __init__(self, dataframe, parent):
        super(DataFrameModel, self).__init__(parent)
        self.dataframe = dataframe
        self.colnames = self.dataframe.columns
        self.roles = {}
        
    def rowCount(self, parent):
        return self.dataframe.shape[0]
    
    def columnCount(self, parent):
        return self.dataframe.shape[1]
    
    def data(self, index, role = Qt.DisplayRole):
        row = index.row()
        col = index.column()
        colname = self.colnames[col]
        if role == Qt.DisplayRole:
            val = self.dataframe.get_value(row, colname)
            if isinstance(val, str) or isinstance(val, unicode):
                return QString(val)
            else:
                if isnan(val):
                    return QString("NaN")
                elif isinf(val):
                    return QString("Inf")
                else:
                    if abs(val) <= 1:
                        return QVariant(('%.3g' % val))
                    else:
                        return QVariant(int(round(val)))            
        elif role == Qt.TextAlignmentRole:
            return QVariant(Qt.AlignRight | Qt.AlignVCenter)
                    
    
    def headerData(self, section, orientation, role):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                return QVariant(self.colnames[section])
            if orientation == Qt.Vertical:
                return section + 1

    def clear(self):
        self.dataframe = DataFrame()
        self.columns = []
        self.reset()
        
        

class OfTableView(QTableView):
    def __init__(self, parent = None):
        super(OfTableView, self).__init__(parent)
        
    def copy(self):
        '''
        Copy the table selection to the clipboard
        '''
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()
        indexes.sort()
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
            previous = current
        selected_text.append('\n')
        QApplication.clipboard().setText(selected_text)

class OfSs:
    '''a container for stylesheets'''
        
    bold_center = '''
        QLabel {
            font-weight: bold; 
            qproperty-alignment: AlignCenter;
        }'''

    dock_style = '''
         QDockWidget {
             margin: 5px;
             background : #e6ebf4;
         }
        
         QDockWidget::title {
             margin: 2px;
             padding-left: 2px;
             background-color: #e7d2d9;
             border : 1px solid rgb(166, 54, 110);
         }        
         '''
    declaration_page_style = '''
        QDialog{
            background-color: #e6ebf4;
        }
        /*----------------- Objets----------------- */        
        QLineEdit{
            border: 1px solid gray;
            border-style: solid;
            border-radius: 2px;
            padding: 0 4px;
            background: white;
            selection-background-color: darkgray;
        }
        QSpinBox{
            border: 1px solid gray;
            border-style: solid;
            border-radius: 2px;
            padding: 0 4px;
            background: white;
            selection-background-color: darkgray;
            alignment: alignright;
        }
        QDateEdit{
            border: 1px solid gray;
            border-style: solid;
            border-radius: 2px;
            padding: 0 4px;
            background: white;
            selection-background-color: darkgray;
        }
            
        /*-----------------Textes----------------- */
        /*  Titres */

        QLabel.titreA{
            color: rgb(166, 54, 110);
            font: Arial;
            font-size : 20px;
            font-weight : normal;
        }
        QLabel.titreB{
            color: rgb(166, 54, 110);
            font: Arial;
            font-size : 12px;
            font-weight : bold;
        }
        QLabel.titreC{
            color: rgb(166, 54, 110);
            font: Arial;
            font-size : 12px;
            font-weight : normal;
        }
        QLabel.titreD{
            color: rgb(166, 54, 110);
            font: Arial;
            font-size : 9px;
            font-weight : normal;
        }

        /*  Textes */

        QLabel.texte01{
            font-size: 11px;
        }
        QLabel.texte02{
            font-size: 9px;
        }
        QLabel.code{
            font-size: 12px;
            font-weight : bold;
        }
        
        /*----------------- Design----------------- */
        /*------  page  declaration.ui------*/
        
        /*  boite générale */
        QLabel.sponsor{
            background-image: url(:/images/logo1.png);  
        }
        
        QFrame.top{
            background-color: #e7d2d9;
            border: 2px solid #e7d2d9;
            border-radius: 6px;
        }
        
        /*  Pages du formulaire */
        QLabel.boite1{
            background-color: #e7d2d9;
            border-top: 2px solid #e7d2d9;
            border-left: 2px solid #e7d2d9;
            border-right: 2px solid #e7d2d9;
            border-top-left-radius: 6px;
            border-top-right-radius: 6px;
            font-size: 20px;
            text-align:center;
            font: bold;
            color: #ffffff;
        }
        QListView {
            border-left: 2px solid #e7d2d9;
            border-right: 2px solid #e7d2d9;
            border-bottom: 2px solid #e7d2d9;
            font-size: 10px;
            border-bottom-left-radius: 6px;
            border-bottom-right-radius: 6px;
        }

        QScrollArea{
            border : 0px;
        }
        
        QStackedWidget{
            background-color: #e6ebf4;
            border : 0px;
        }
        
        '''

    
### Some useful widgets

class MySpinBox(QWidget):
    def __init__(self, parent, prefix = None, suffix = None, option = None, min_ = None, max_ = None,
                 step = None, tip = None, value = None, changed =None):
        super(MySpinBox, self).__init__(parent)
    
        if prefix:
            plabel = QLabel(prefix)
        else:
            plabel = None
        if suffix:
            slabel = QLabel(suffix)
        else:
            slabel = None
        spinbox = QSpinBox(parent)
        if min_ is not None:
            spinbox.setMinimum(min_)
        if max_ is not None:
            spinbox.setMaximum(max_)
        if step is not None:
            spinbox.setSingleStep(step)
        if tip is not None:
            spinbox.setToolTip(tip)
        layout = QHBoxLayout()
        for subwidget in (plabel, spinbox, slabel):
            if subwidget is not None:
                layout.addWidget(subwidget)
        if value is not None:
            spinbox.setValue(value)
        
        if changed is not None:
            self.connect(spinbox, SIGNAL('valueChanged(int)'), changed)

        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.spin = spinbox




            
class MyDoubleSpinBox(QWidget):
    def __init__(self, parent, prefix = None, suffix = None, option = None, min_ = None, max_ = None,
                 step = None, tip = None, value = None, changed =None):
        super(MyDoubleSpinBox, self).__init__(parent)
    
        if prefix:
            plabel = QLabel(prefix)
        else:
            plabel = None
        if suffix:
            slabel = QLabel(suffix)
        else:
            slabel = None
        spinbox = QDoubleSpinBox(parent)
        if min_ is not None:
            spinbox.setMinimum(min_)
        if max_ is not None:
            spinbox.setMaximum(max_)
        if step is not None:
            spinbox.setSingleStep(step)
        if tip is not None:
            spinbox.setToolTip(tip)
        layout = QHBoxLayout()
        for subwidget in (plabel, spinbox, slabel):
            if subwidget is not None:
                layout.addWidget(subwidget)
        if value is not None:
            spinbox.setValue(value)
        
        if changed is not None:
            self.connect(spinbox, SIGNAL('valueChanged(double)'), changed)

        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.spin = spinbox

class MyComboBox(QWidget):
    def __init__(self, parent, text, choices = None, option = None, tip = None):
        super(MyComboBox, self).__init__(parent)
        """choices: couples (name, key)"""
        label = QLabel(text)
        combobox = QComboBox(parent)
        if tip is not None:
            combobox.setToolTip(tip)
        if choices:
            for name, key in choices:
                combobox.addItem(name, QVariant(key))
        layout = QHBoxLayout()
        for subwidget in (label, combobox):
            layout.addWidget(subwidget)
        layout.addStretch(1)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        self.box = combobox



# TODO should improve qtpandas 
from pandas import Index

def testDf():
    ''' creates test dataframe '''
    data = {'int':[1,2,3], 'float':[1.5,2.5,3.5],
            'string':['a','b','c'], 'nan':[np.nan,np.nan,np.nan]}
    return DataFrame(data, index=Index(['AAA','BBB','CCC']),
                     columns=['int','float','string','nan'])


from pandas.sandbox.qtpandas import DataFrameWidget
from PyQt4.QtGui import (QDialog, QVBoxLayout)


class Form(QDialog):
    def __init__(self,parent=None):
        super(Form,self).__init__(parent)

        df = testDf() # make up some data
        widget = DataFrameWidget(df)
        widget.resizeColumnsToContents()

        layout = QVBoxLayout()
        layout.addWidget(widget)
        self.setLayout(layout)

if __name__=='__main__':
    import sys
    import numpy as np

    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()





