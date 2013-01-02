# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/parametres.ui'
#
# Created: Mon Dec 31 15:23:38 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Parametres(object):
    def setupUi(self, Parametres):
        Parametres.setObjectName(_fromUtf8("Parametres"))
        Parametres.resize(400, 300)
        Parametres.setLocale(QtCore.QLocale(QtCore.QLocale.French, QtCore.QLocale.France))
        self.dockWidgetContents = QtGui.QWidget()
        self.dockWidgetContents.setObjectName(_fromUtf8("dockWidgetContents"))
        self.verticalLayout = QtGui.QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setSpacing(2)
        self.verticalLayout.setMargin(2)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(2)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.save_btn = QtGui.QPushButton(self.dockWidgetContents)
        self.save_btn.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/document-save.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.save_btn.setIcon(icon)
        self.save_btn.setIconSize(QtCore.QSize(22, 22))
        self.save_btn.setObjectName(_fromUtf8("save_btn"))
        self.horizontalLayout.addWidget(self.save_btn)
        self.open_btn = QtGui.QPushButton(self.dockWidgetContents)
        self.open_btn.setText(_fromUtf8(""))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/document-open.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.open_btn.setIcon(icon1)
        self.open_btn.setIconSize(QtCore.QSize(22, 22))
        self.open_btn.setObjectName(_fromUtf8("open_btn"))
        self.horizontalLayout.addWidget(self.open_btn)
        self.line = QtGui.QFrame(self.dockWidgetContents)
        self.line.setFrameShape(QtGui.QFrame.VLine)
        self.line.setFrameShadow(QtGui.QFrame.Sunken)
        self.line.setObjectName(_fromUtf8("line"))
        self.horizontalLayout.addWidget(self.line)
        self.reset_btn = QtGui.QPushButton(self.dockWidgetContents)
        self.reset_btn.setMinimumSize(QtCore.QSize(0, 30))
        self.reset_btn.setText(_fromUtf8(""))
        icon2 = QtGui.QIcon()
        icon2.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/view-refresh.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.reset_btn.setIcon(icon2)
        self.reset_btn.setIconSize(QtCore.QSize(22, 22))
        self.reset_btn.setObjectName(_fromUtf8("reset_btn"))
        self.horizontalLayout.addWidget(self.reset_btn)
        spacerItem = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.label = QtGui.QLabel(self.dockWidgetContents)
        self.label.setText(_fromUtf8(""))
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.uiTree = QtGui.QTreeView(self.dockWidgetContents)
        self.uiTree.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.uiTree.setAlternatingRowColors(True)
        self.uiTree.setIndentation(10)
        self.uiTree.setObjectName(_fromUtf8("uiTree"))
        self.verticalLayout.addWidget(self.uiTree)
#        Parametres.setWidget(self.dockWidgetContents)

        self.retranslateUi(Parametres)
        QtCore.QMetaObject.connectSlotsByName(Parametres)

    def retranslateUi(self, Parametres):
        Parametres.setWindowTitle(QtGui.QApplication.translate("Parametres", "Paramètres", None, QtGui.QApplication.UnicodeUTF8))
        self.save_btn.setToolTip(QtGui.QApplication.translate("Parametres", "Enregistrer les paramètres actuels", None, QtGui.QApplication.UnicodeUTF8))
        self.open_btn.setToolTip(QtGui.QApplication.translate("Parametres", "Ouvrir des paramètres", None, QtGui.QApplication.UnicodeUTF8))
        self.reset_btn.setToolTip(QtGui.QApplication.translate("Parametres", "Reset", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setToolTip(QtGui.QApplication.translate("Parametres", "datesim", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
