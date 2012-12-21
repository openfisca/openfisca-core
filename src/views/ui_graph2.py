# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/graph2.ui'
#
# Created: Tue Nov 08 17:13:20 2011
#      by: PyQt4 UI code generator 4.8.5
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Graph(object):
    def setupUi(self, Graph):
        Graph.setObjectName(_fromUtf8("Graph"))
        Graph.resize(645, 552)
        Graph.setWindowTitle(QtGui.QApplication.translate("Graph", "Graph", None, QtGui.QApplication.UnicodeUTF8))
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.gv = QtGui.QGraphicsView(self.dockWidgetContents)
        self.gv.setObjectName(_fromUtf8("gv"))
        self.verticalLayout.addWidget(self.gv)
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.option_btn = QtGui.QPushButton(self.dockWidgetContents)
        self.option_btn.setToolTip(QtGui.QApplication.translate("Graph", "Affichage et couleurs du graphique", None, QtGui.QApplication.UnicodeUTF8))
        self.option_btn.setText(QtGui.QApplication.translate("Graph", "Options", None, QtGui.QApplication.UnicodeUTF8))
        self.option_btn.setObjectName(_fromUtf8("option_btn"))
        self.horizontalLayout.addWidget(self.option_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        Graph.setWidget(self.dockWidgetContents)

        self.retranslateUi(Graph)
        QtCore.QMetaObject.connectSlotsByName(Graph)

    def retranslateUi(self, Graph):
        pass

