# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/aggregate_output.ui'
#
# Created: Tue Feb 21 15:07:20 2012
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Aggregate_Output(object):
    def setupUi(self, Aggregate_Output):
        Aggregate_Output.setObjectName(_fromUtf8("Aggregate_Output"))
        Aggregate_Output.resize(567, 405)
        Aggregate_Output.setWindowTitle(QtGui.QApplication.translate("Aggregate_Output", "Aggregate Output", None, QtGui.QApplication.UnicodeUTF8))
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label = QtGui.QLabel(self.dockWidgetContents)
        self.label.setText(QtGui.QApplication.translate("Aggregate_Output", "Résultat aggregé de la simulation", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setObjectName(_fromUtf8("label"))
        self.verticalLayout.addWidget(self.label)
        self.aggregate_view = QtGui.QTableView(self.dockWidgetContents)
        self.aggregate_view.setObjectName(_fromUtf8("aggregate_view"))
        self.verticalLayout.addWidget(self.aggregate_view)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label_2 = QtGui.QLabel(self.dockWidgetContents)
        self.label_2.setText(QtGui.QApplication.translate("Aggregate_Output", "Distribution de l\'impact par", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.distribution_combo = QtGui.QComboBox(self.dockWidgetContents)
        self.distribution_combo.setObjectName(_fromUtf8("distribution_combo"))
        self.distribution_combo.addItem(_fromUtf8(""))
        self.distribution_combo.setItemText(0, QtGui.QApplication.translate("Aggregate_Output", "déciles", None, QtGui.QApplication.UnicodeUTF8))
        self.distribution_combo.addItem(_fromUtf8(""))
        self.distribution_combo.setItemText(1, QtGui.QApplication.translate("Aggregate_Output", "types de famille", None, QtGui.QApplication.UnicodeUTF8))
        self.horizontalLayout.addWidget(self.distribution_combo)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.distribution_view = QtGui.QTableView(self.dockWidgetContents)
        self.distribution_view.setObjectName(_fromUtf8("distribution_view"))
        self.verticalLayout.addWidget(self.distribution_view)
        Aggregate_Output.setWidget(self.dockWidgetContents)

        self.retranslateUi(Aggregate_Output)
        QtCore.QMetaObject.connectSlotsByName(Aggregate_Output)

    def retranslateUi(self, Aggregate_Output):
        pass

