# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/baremedialog.ui'
#
# Created: Tue Nov 27 17:24:33 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_BaremeDialog(object):
    def setupUi(self, BaremeDialog):
        BaremeDialog.setObjectName(_fromUtf8("BaremeDialog"))
        BaremeDialog.resize(549, 308)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(BaremeDialog.sizePolicy().hasHeightForWidth())
        BaremeDialog.setSizePolicy(sizePolicy)
        BaremeDialog.setMinimumSize(QtCore.QSize(549, 308))
        BaremeDialog.setMaximumSize(QtCore.QSize(549, 16777215))
        BaremeDialog.setSizeGripEnabled(False)
        self.gridLayout = QtGui.QGridLayout(BaremeDialog)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.marLabel = QtGui.QLabel(BaremeDialog)
        self.marLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.marLabel.setObjectName(_fromUtf8("marLabel"))
        self.gridLayout.addWidget(self.marLabel, 0, 0, 1, 3)
        self.moyLabel = QtGui.QLabel(BaremeDialog)
        self.moyLabel.setAlignment(QtCore.Qt.AlignCenter)
        self.moyLabel.setObjectName(_fromUtf8("moyLabel"))
        self.gridLayout.addWidget(self.moyLabel, 0, 3, 1, 2)
        self.marView = QtGui.QTableView(BaremeDialog)
        self.marView.setObjectName(_fromUtf8("marView"))
        self.gridLayout.addWidget(self.marView, 1, 0, 1, 3)
        self.moyView = QtGui.QTableView(BaremeDialog)
        self.moyView.setObjectName(_fromUtf8("moyView"))
        self.gridLayout.addWidget(self.moyView, 1, 3, 1, 2)
        spacerItem = QtGui.QSpacerItem(195, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem, 2, 0, 1, 1)
        self.add_btn = QtGui.QPushButton(BaremeDialog)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.add_btn.sizePolicy().hasHeightForWidth())
        self.add_btn.setSizePolicy(sizePolicy)
        self.add_btn.setMinimumSize(QtCore.QSize(0, 0))
        self.add_btn.setMaximumSize(QtCore.QSize(23, 23))
        self.add_btn.setText(_fromUtf8(""))
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/list-add.png")), QtGui.QIcon.Normal, QtGui.QIcon.On)
        self.add_btn.setIcon(icon)
        self.add_btn.setIconSize(QtCore.QSize(16, 16))
        self.add_btn.setObjectName(_fromUtf8("add_btn"))
        self.gridLayout.addWidget(self.add_btn, 2, 1, 1, 1)
        self.rmv_btn = QtGui.QPushButton(BaremeDialog)
        self.rmv_btn.setMinimumSize(QtCore.QSize(23, 23))
        self.rmv_btn.setMaximumSize(QtCore.QSize(23, 23))
        self.rmv_btn.setText(_fromUtf8(""))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(_fromUtf8(":/images/list-remove.png")), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.rmv_btn.setIcon(icon1)
        self.rmv_btn.setObjectName(_fromUtf8("rmv_btn"))
        self.gridLayout.addWidget(self.rmv_btn, 2, 2, 1, 1)
        spacerItem1 = QtGui.QSpacerItem(163, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.gridLayout.addItem(spacerItem1, 2, 3, 1, 1)
        self.buttonBox = QtGui.QDialogButtonBox(BaremeDialog)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.gridLayout.addWidget(self.buttonBox, 2, 4, 1, 1)

        self.retranslateUi(BaremeDialog)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), BaremeDialog.accept)
        QtCore.QMetaObject.connectSlotsByName(BaremeDialog)

    def retranslateUi(self, BaremeDialog):
        BaremeDialog.setWindowTitle(QtGui.QApplication.translate("BaremeDialog", "Barème", None, QtGui.QApplication.UnicodeUTF8))
        self.marLabel.setText(QtGui.QApplication.translate("BaremeDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">Tranches de taux marginaux</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))
        self.moyLabel.setText(QtGui.QApplication.translate("BaremeDialog", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><span style=\" font-size:10pt; font-weight:600;\">Tranches de taux moyens</span></p></body></html>", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
