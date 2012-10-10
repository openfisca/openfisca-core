# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/graph.ui'
#
# Created: Fri Oct 05 18:24:46 2012
#      by: PyQt4 UI code generator 4.9.1
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
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.taux_btn = QtGui.QCheckBox(self.dockWidgetContents)
        self.taux_btn.setObjectName(_fromUtf8("taux_btn"))
        self.horizontalLayout.addWidget(self.taux_btn)
        self.absBox = QtGui.QComboBox(self.dockWidgetContents)
        self.absBox.setObjectName(_fromUtf8("absBox"))
        self.horizontalLayout.addWidget(self.absBox)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.hidelegend_btn = QtGui.QPushButton(self.dockWidgetContents)
        self.hidelegend_btn.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/legende.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.hidelegend_btn.setIcon(icon)
        self.hidelegend_btn.setIconSize(QtCore.QSize(22, 22))
        self.hidelegend_btn.setCheckable(True)
        self.hidelegend_btn.setObjectName(_fromUtf8("hidelegend_btn"))
        self.horizontalLayout.addWidget(self.hidelegend_btn)
        self.option_btn = QtGui.QPushButton(self.dockWidgetContents)
        self.option_btn.setObjectName(_fromUtf8("option_btn"))
        self.horizontalLayout.addWidget(self.option_btn)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.mplwidget = MatplotlibWidget(self.dockWidgetContents)
        self.mplwidget.setObjectName(_fromUtf8("mplwidget"))
        self.verticalLayout.addWidget(self.mplwidget)
        Graph.setWidget(self.dockWidgetContents)

        self.retranslateUi(Graph)
        QtCore.QMetaObject.connectSlotsByName(Graph)

    def retranslateUi(self, Graph):
        Graph.setWindowTitle(QtGui.QApplication.translate("Graph", "Graphique", None, QtGui.QApplication.UnicodeUTF8))
        self.taux_btn.setToolTip(QtGui.QApplication.translate("Graph", "Voir les taux moyens et marginaux d\'imposition", None, QtGui.QApplication.UnicodeUTF8))
        self.taux_btn.setText(QtGui.QApplication.translate("Graph", "Taux moyens\n"
"Taux marginaux", None, QtGui.QApplication.UnicodeUTF8))
        self.hidelegend_btn.setToolTip(QtGui.QApplication.translate("Graph", "Masquer la légende", None, QtGui.QApplication.UnicodeUTF8))
        self.option_btn.setToolTip(QtGui.QApplication.translate("Graph", "Affichage et couleurs du graphique", None, QtGui.QApplication.UnicodeUTF8))
        self.option_btn.setText(QtGui.QApplication.translate("Graph", "Options", None, QtGui.QApplication.UnicodeUTF8))

from widgets.matplotlibwidget import MatplotlibWidget
import resources_rc
