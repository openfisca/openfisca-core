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

import os
import sys
import numpy as np
import datetime
from Config import CONF
from pylab import hist, setp
from pandas import read_csv

from PyQt4.QtCore import SIGNAL, Qt, QAbstractTableModel, QModelIndex, QVariant
from PyQt4.QtGui import (QWidget, QLabel, QApplication, QHBoxLayout, QVBoxLayout, 
                         QPushButton, QDoubleSpinBox, QTableView, QInputDialog)
import guidata.dataset.datatypes as dt
import guidata.dataset.dataitems as di
from widgets.matplotlibwidget import MatplotlibWidget

from core.datatable import DataTable, SystemSf
from parametres.paramData import XmlReader, Tree2Object
from france.model import ModelFrance
from france.data import InputTable, BoolCol, AgesCol, EnumCol
        
class MainWindow(QWidget):
    def __init__(self, parent = None):
        super(MainWindow, self).__init__(parent)
        #print os.listdir('../../cas/')
        # cas MBJ
        filename = 'C:/Users/Utilisateur/Documents/Data/R/openfisca/2006/final.csv' 
        # cas CS
        # filename = 'C:/Users/Utilisateur/Desktop/calmar/final.csv'
        # maison MBJ 
        #filename = '../../cas/final2.csv'
        # load micro data
        
        self.loadData(filename)
        self.date = datetime.date(2006,01,01)
        
        # set MainWindow layout and add children to it
        self.lyt = QVBoxLayout()
        
        # calibration widget
        self.param = {'method': 'logit', 'up':3, 'lo':.33, 'use_proportions':True}
        calib_btn = QPushButton(u'Calibrer', self)
        param_btn = QPushButton(u'Choisir la méthode', self)
        self.setParamLabel()
        calib_lyt = QHBoxLayout()
        calib_lyt.addWidget(calib_btn)
        calib_lyt.addWidget(param_btn)
        calib_lyt.addWidget(self.param_label)
        self.lyt.addLayout(calib_lyt)

        self.connect(calib_btn, SIGNAL('clicked()'), self.calibrate)
        self.connect(param_btn, SIGNAL('clicked()'), self.setParam)

        # margins 
        margins = Margins(self.inputs)

        data_dir = CONF.get('paths', 'data_dir')
        year = CONF.get('simulation','datesim')[:4]
        if int(year) <= 2008:
            print 'calage'
            # update weights with calmar (demography)
            fname_men = os.path.join(data_dir, 'calage_men.csv')
            f_tot = open(fname_men)
            totals = read_csv(f_tot,index_col = (0,1))

            marges = {}
            for var, mod in totals.index:
                if not marges.has_key(var):
                    marges[var] = {}
                
                marges[var][mod] =  totals.get_value((var,mod),year)
                if var == 'totalpop': 
                    totalpop = marges.pop('totalpop')[0]
                    # TODO
                else:
                    margins.addVar(var, marges[var])
            f_tot.close()


        
        self.margins_model = MarginsModel(margins, self)
        self.margins_view = QTableView(self)
        self.margins_view.setModel(self.margins_model)
        self.margins_dict = self.margins_model._margins.get_calib_vars()        
        
        #   buttons to add and rmv margins
        add_margin_btn = QPushButton('add', self)
        rmv_margin_btn = QPushButton('rmv', self)
        margin_btn_lyt = QHBoxLayout()
        margin_btn_lyt.addWidget(add_margin_btn)
        margin_btn_lyt.addWidget(rmv_margin_btn)
        self.connect(add_margin_btn, SIGNAL('clicked()'), self.add_margin)
        self.connect(rmv_margin_btn, SIGNAL('clicked()'), self.rmv_margin)

        # outputs
        self.model = self.getModel()
        self.outputs = Outputs(self.model, self.inputs)
        self.outputs_model = OutputsModel(self)
        self.outputs_view = QTableView(self)
        self.outputs_view.setModel(self.outputs_model)
        self.outputs_dict = self.outputs.get_vars()
        #   buttons to add and rmv outputs
        add_output_btn = QPushButton('add', self)
        rmv_output_btn = QPushButton('rmv', self)
        output_btn_lyt = QHBoxLayout()
        output_btn_lyt.addWidget(add_output_btn)
        output_btn_lyt.addWidget(rmv_output_btn)
        self.connect(add_output_btn, SIGNAL('clicked()'), self.add_output)
        self.connect(rmv_output_btn, SIGNAL('clicked()'), self.rmv_output)

        
        # Widgets in layout
        self.lyt.addWidget(self.margins_view)
        self.lyt.addLayout(margin_btn_lyt)

        # weights ratio plotsplot        
        self.mplwidget = MatplotlibWidget(self)
        self.lyt.addWidget(self.mplwidget)
        
        self.lyt.addWidget(self.outputs_view)
        self.lyt.addLayout(output_btn_lyt)
        
        self.setLayout(self.lyt)
        
        
                

    def add_margin(self):
        self.margins_model.add_margin()
    
    def rmv_margin(self):
        self.margins_model.rmv_margin()
        
    def add_output(self):
        self.outputs_model.add_output()
    
    def rmv_output(self):
        self.outputs_model.rmv_output()    
        
    def setParam(self):
        up, lo = 1, 1
        method, ok = QInputDialog.getItem(self.parent(), u"Choix de la méthode", u"Nom de la méthode", 
                                           list(['linear', 'raking ratio', 'logit']))
        if method == "logit":
            up, ok1 = QInputDialog.getDouble(self.parent(), u"Paramètre up", u"Augmentation maximale du ratio", 
                                           min=1,decimals=3)
            lo, ok2 = QInputDialog.getDouble(self.parent(), u"Paramètre lo", u"Diminution minimale du ratio", 
                                           max=1, min=0,decimals=3)            
            ok = ok & ok1 & ok2    
        
        self.param = {'method': method, 'up': up, 'lo': lo , 'use_proportions': True, 'pondini':'wprm_init'}        
        if ok: self.setParamLabel()
        return ok

    def setParamLabel(self):
        ok = False
        method = self.param['method']
        up = self.param['up']
        lo = self.param['lo']
        if method == "logit":
            param_label_string = u"méthode: %s, (up: %.2f, lo: %.2f)" % (method, up, lo)
            ok = True            
        elif method == "linear" or method == "raking ratio":    
            param_label_string = u"méthode: %s" % method
            ok = True
        if hasattr(self,'param_label'): self.param_label.setText(param_label_string)
        else: self.param_label = QLabel(param_label_string)
        return ok

    def loadData(self, filename):
        
        self.inputs = DataTable(InputTable, external_data = filename)
        self.inputs.gen_index(['men', 'fam', 'foy'])
        print 'loading finished'
        
    def getModel(self):
        date = self.date
        reader = XmlReader('data/param.xml', date)
        P = Tree2Object(reader.tree)
        P.datesim = date
        model = SystemSf(ModelFrance, P, P) # TODO homogeneize notations: model is called population in MainWindow
        model.set_inputs(self.inputs)
        return model
        
    def calibrate(self):
        self.margins_dict = self.margins_model._margins.get_calib_vars()
        
        self.margins_model._margins._marges_new = self.inputs.update_weights(self.margins_dict,param=self.param, return_margins = True)
#        inputs = self.inputs
#        
#        self.model.set_inputs(inputs)
        self.margins_model.update_margins()
        
        print self.outputs._vars
        self.outputs_model.update_outputs()
    
        weight_ratio = self.inputs.get_value('wprm')/self.inputs.get_value('wprm_init')
    
        print 'low ratios: ',  np.sort(weight_ratio)[1:5]
        print 'large ratios : ' ,  np.sort(weight_ratio)[-5:]
        
        self.plotWeightsRatios()
            
    def plotWeightsRatios(self):
        ax = self.mplwidget.axes
        ax.clear()
        weight_ratio = self.inputs.get_value('wprm')/self.inputs.get_value('wprm_init')
        ax.hist(weight_ratio, 50, normed=1, histtype='stepfilled')
        ax.set_xlabel(u"Poids relatifs")
        ax.set_ylabel(u"Densité")
        self.mplwidget.draw()

class MarginsModel(QAbstractTableModel):
    def __init__(self, margins, parent = None):
        super(MarginsModel, self).__init__(parent)
        self._parent = parent
        self._margins = margins
        self._marges_new = {}
    
    def parent(self):
        return self._parent
    
    def rowCount(self, parent = QModelIndex()):
        return self._margins.rowCount()
    
    def columnCount(self, parent =QModelIndex()):
        return self._margins.columnCount()
    
    def flags(self, index):
        col = index.column()
        if col == 1:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable
        else:
            return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0 : return  "Variable"
                elif section == 1: return "Cible"
                elif section == 2: return u"Cible ajustée"
                elif section == 3: return u"Marge calibrée"
                elif section == 4: return "Marge initiale"        
        
        return super(MarginsModel, self).headerData(section, orientation, role)
    
    def data(self, index, role =  Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole or role == Qt.EditRole:
            return QVariant(self._margins.data(row, col))
        
        if role == Qt.TextAlignmentRole:
            if col != 0: return Qt.AlignRight
        
        return QVariant()

    def setData(self, index, value, role = Qt.EditRole):
        if not index.isValid():
            return False
        row = index.row()
        col = index.column()
        if role == Qt.EditRole:
            if col == 1: self._margins.setData(row, col, value.toPyObject())
            self.dataChanged.emit(index, index)
            return True
        return False

    def add_margin(self):
        varname, ok = QInputDialog.getItem(self.parent(), "Add variable", "Name of the variable to be added", 
                                           sorted(list(self._margins._inputs.col_names)))
        insertion = ok and not(varname.isEmpty()) and (varname not in self._margins._vars)
        if insertion :
            nbrow = self._margins.howManyFields(str(varname))
            self._margin_to_insert = str(varname)
            self.insertRows(0,nbrow-1)
            del self._margin_to_insert
    
    def rmv_margin(self):
        varname, ok = QInputDialog.getItem(self.parent(), "Remove variable", "Name of the variable to be removed", 
                                           sorted(self.parent().margins_dict))
        deletion = ok and not(varname.isEmpty())
        if deletion: 
            nbrow = self._margins.howManyFields(str(varname))
            self._margin_to_remove = str(varname)
            self.removeRows(0,nbrow-1)    
            del self._margin_to_remove

    def update_margins(self):
        self.beginResetModel()
        self._margins._vars = []
        for var, target in self._margins._vars_dict.iteritems():
            self._margins.addVar(var, target)
        self.endResetModel()

    def insertRows(self, row, count, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row + count)
        self._margins.addVar(self._margin_to_insert,None)
        self.endInsertRows()
        return True
    
    def removeRows(self, row, count, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row + count)
        self._margins.rmvVar(str(self._margin_to_remove))
        self.endRemoveRows()
        return True

class Margins(object):
    def __init__(self, inputs):
        super(Margins, self).__init__()
        self._vars_dict = {} # list of strings with varnames
        self._vars = []       # list of strings with varnames
        self._attr = {}
        self._inputs = inputs
        self._marges_new = {}

    def get_calib_vars(self):
        return self._vars_dict    

    def rowCount(self):
        return len(self._vars)
    
    def columnCount(self):
        return 5
        
    def data(self, row, col):
        var = str(self._vars[row])
        if   col == 0: return  var
        elif col == 1: return self._attr[var][0] 
        elif col == 2: return self._attr[var][1] 
        elif col == 3: return self._attr[var][2] 
        elif col == 4: return self._attr[var][3] 

        
    def setData(self, row, col, value):
        var = self._vars[row]
        if col == 1: self._attr[var][0] = value
        #if col == 2: self._attr[var][1] = value
        
        if var in self._vars_dict:
            self.updateVarDict(var, value)
        else:
            varname, modality = var.split('_')
            self.updateVarDict(varname, value, modality)

    def howManyFields(self, varname):
        varcol = self._inputs.description.get_col(varname)
        if isinstance(varcol , BoolCol):
            return 2
        elif isinstance(varcol , AgesCol):
            return len(np.unique(varcol.get_value()))
        elif isinstance(varcol , EnumCol):
            return varcol.enum._count  
        else:
            return 1        

    def addVar(self, varname, target=None):
        varcol = self._inputs.description.get_col(varname)
        if isinstance(varcol , BoolCol):
            if target is not None:
                ok1 = self.addVar2(varname, True,  target['True'])
                ok0 = self.addVar2(varname, False, target['False'])
            else:
                ok1 = self.addVar2(varname, True)
                ok0 = self.addVar2(varname, False)    
            return ok1 and ok0
        if isinstance(target , dict):
            modalities = target.keys()
            ok = True
            for modality in modalities:
                if target is not None: 
                    ok2 = self.addVar2(varname, modality, target[modality])
                else:
                    ok2 = self.addVar2(varname, modality)
                ok = ok and ok2 
            return ok
        if isinstance(varcol, EnumCol):
            ok = True
            for modality, index in varcol.enum.itervars():
                ok2 = self.addVar2(varname, modality)
                ok = ok and ok2 
            return ok    
        else:
            ok = self.addVar2(varname, None, target)
            return ok

    def addVar2(self, varname, modality = None, target=None):
        if modality is not None:
            varname_mod = "%s_%s" % (varname, modality)
        else:
            varname_mod = varname
        if varname_mod in self._vars:
            return False
        # elif varname not in self._inputs.col_names:
        # raise Exception("The variable %s is not present in the inputs table" % varname)
        # return None
        self._vars.append(varname_mod)
        w_init = self._inputs.get_value("wprm_init", self._inputs.index['men'])
        w = self._inputs.get_value("wprm", self._inputs.index['men'])
        varcol = self._inputs.description.get_col(varname) 
        value = self._inputs.get_value(varname, self._inputs.index['men'])
        if modality is not None:     
            if isinstance(varcol, EnumCol):
                total = sum(w*(value == varcol.enum[modality]))
                total_init = sum(w_init*(value == varcol.enum[modality]))
            else:    
                total = sum(w*(value == modality))
                total_init = sum(w_init*(value == modality))
        else: 
            total = sum(w*value)
            total_init = sum(w_init*value)
        if not target: 
            target = 0
        if varname_mod in self._marges_new.keys(): # TODO
            new_target = self._marges_new[varname_mod]
        else:
            new_target = 0        
        self._attr[varname_mod] = [float(target), float(new_target), float(total) , float(total_init)]
        
        self.updateVarDict(varname, target, modality)
        
        return True

    def rmvVar(self, varname):
        
        if not varname in self._vars_dict:
            return None

        if isinstance(self._vars_dict[varname], dict):
            for modality in self._vars_dict[varname].iterkeys():
                var_to_remove = "%s_%s" % (varname, modality)
                ind = self._vars.index(var_to_remove)
                self._vars.pop(ind)
                del self._attr[var_to_remove]
        else: 
            var_to_remove = varname
            ind = self._vars.index(var_to_remove)
            self._vars.pop(ind)
            del self._attr[var_to_remove]
        del self._vars_dict[varname]
        
    def updateVarDict(self, varname, target, modality=None):
        if modality is not None:
            if varname not in self._vars_dict:
                self._vars_dict[varname] = {modality: target}
            else:
                self._vars_dict[varname][modality] = target
        else:
            self._vars_dict[varname] = target         

##########

class OutputsModel(QAbstractTableModel):
    def __init__(self, parent = None):
        super(OutputsModel, self).__init__(parent)
        self._parent = parent
        self._outputs = parent.outputs
    
    def parent(self):
        return self._parent
    
    def rowCount(self, parent = QModelIndex()):
        return self._outputs.rowCount()
    
    def columnCount(self, parent =QModelIndex()):
        return self._outputs.columnCount()
    
    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    
    def headerData(self, section, orientation, role = Qt.DisplayRole):
        if role == Qt.DisplayRole:
            if orientation == Qt.Horizontal:
                if section == 0 : return  u"Variable"
                elif section == 1: return u"Total après calibration"
                elif section == 2: return u"Total initial"
        
        return super(OutputsModel, self).headerData(section, orientation, role)
    
    def data(self, index, role =  Qt.DisplayRole):
        if not index.isValid():
            return QVariant()
        row = index.row()
        col = index.column()
        if role == Qt.DisplayRole:
            return QVariant(self._outputs.data(row, col))
        return QVariant()

    def add_output(self):
        varname, ok = QInputDialog.getItem(self.parent(), "Add variable", "Name of the variable to be added",
                                           sorted(list(self._outputs.model.col_names)))
        insertion = ok and not(varname.isEmpty()) and (varname not in self._outputs._vars)
        if insertion :
            self._output_to_insert = str(varname)
            self.insertRow(0)
            del self._output_to_insert
    
    def rmv_output(self):
        varname, ok = QInputDialog.getItem(self.parent(), "Remove variable", "Name of the variable to be removed",
                                           self._outputs._vars)
        deletion = ok and not(varname.isEmpty())
        if deletion: 
            self._output_to_remove = str(varname)
            self.removeRow(0)    
            del self._output_to_remove

    def update_outputs(self):       
        self.beginResetModel()
        for var in self._outputs._vars:
            self._outputs.addVar(var)
        self.endResetModel()
           
    def insertRow(self, row, parent = QModelIndex()):
        self.beginInsertRows(parent, row, row)
        self._outputs.addVar(self._output_to_insert)
        self.endInsertRows()
        return True
    
    def removeRow(self, row, parent = QModelIndex()):
        self.beginRemoveRows(parent, row, row)
        self._outputs.rmvVar(self._output_to_remove)
        self.endRemoveRows()
        return True

class Outputs(object):
    def __init__(self, model, inputs):
        super(Outputs, self).__init__()
        self._vars = [] # list of strings with varnames
        self._attr = {} # dict of totals 
        self.model = model
        self.inputs = inputs
        
    def get_vars(self):
        return self._vars    
        
    def rowCount(self):
        return len(self._vars)
    
    def columnCount(self):
        return 3
        
    def data(self, row, col):
        var = str(self._vars[row])
        if   col == 0: return  var
        elif col == 1: return self._attr[var][0] # total after calib
        elif col == 2: return self._attr[var][1] # initial total
        
    def addVar(self, varname):
        self.model.calculate(varname)
        w_init = self.inputs.get_value('wprm_init')
        w = self.inputs.get_value('wprm')
        value = self.model.get_value(varname)
        print value
        calib_total = sum(value*w)
        init_total  = sum(value*w_init)
        if varname not in self._vars: 
            self._vars.append(varname)
        self._attr[varname] = [float(calib_total), float(init_total)]
        print self._attr[varname]

    def rmvVar(self, varname):
        if not varname in self._vars:
            return None
        ind = self._vars.index(varname)
        self._vars.pop(ind)
        del self._attr[varname]
        

                
def main():
    app = QApplication(sys.argv)
    mainWindow = MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()