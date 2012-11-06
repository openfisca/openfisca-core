# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui/declaration.ui'
#
# Created: Sun Nov 04 23:45:48 2012
#      by: PyQt4 UI code generator 4.9.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    _fromUtf8 = lambda s: s

class Ui_Declaration(object):
    def setupUi(self, Declaration):
        Declaration.setObjectName(_fromUtf8("Declaration"))
        Declaration.resize(1000, 545)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Preferred, QtGui.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(Declaration.sizePolicy().hasHeightForWidth())
        Declaration.setSizePolicy(sizePolicy)
        Declaration.setMinimumSize(QtCore.QSize(700, 500))
        Declaration.setMaximumSize(QtCore.QSize(1000, 640))
        Declaration.setStyleSheet(_fromUtf8("QDialog{\n"
"background-color: #e6ebf4;\n"
"}\n"
"/*----------------- Objets----------------- */\n"
"QLineEdit{\n"
"border: 1px solid gray;\n"
"border-style: solid;\n"
"border-radius: 2px;\n"
"padding: 0 4px;\n"
"background: white;\n"
"selection-background-color: darkgray;\n"
"}\n"
"QSpinBox{\n"
"border: 1px solid gray;\n"
"border-style: solid;\n"
"border-radius: 2px;\n"
"padding: 0 4px;\n"
"background: white;\n"
"selection-background-color: darkgray;\n"
"alignment: alignright;\n"
"}\n"
"QDateEdit{\n"
"border: 1px solid gray;\n"
"border-style: solid;\n"
"border-radius: 2px;\n"
"padding: 0 4px;\n"
"background: white;\n"
"selection-background-color: darkgray;\n"
"}\n"
"\n"
"/*-----------------Textes----------------- */\n"
"/*  Titres */\n"
"QLabel.titreA{\n"
"color: rgb(166, 54, 110);\n"
"font: Arial;\n"
"font-size : 20px;\n"
"font-weight : normal;\n"
"border-style:solid;\n"
"border-color:white;\n"
"border-width:5px;\n"
"}\n"
"QLabel.titreB{\n"
"color: rgb(166, 54, 110);\n"
"font: Arial;\n"
"font-size : 14px;\n"
"font-weight : normal;\n"
"text-decoration:underline\n"
"}\n"
"QLabel.titreC{\n"
"color: rgb(166, 54, 110);\n"
"font: Arial;\n"
"font-size : 12px;\n"
"font-weight : normal;\n"
"}\n"
"QLabel.titreD{\n"
"color: rgb(166, 54, 110);\n"
"font: Arial;\n"
"font-size : 9px;\n"
"font-weight : normal;\n"
"}\n"
"\n"
"/*----------------- Design----------------- */\n"
"/*------  page  declaration.ui------*/\n"
"\n"
"/*  boite générale */\n"
"QLabel.sponsor{\n"
"background-image: url(:/images/logo1.png);  \n"
"}\n"
"\n"
"QFrame.top{\n"
"background-color: #e7d2d9;\n"
"border: 2px solid #e7d2d9;\n"
"border-radius: 6px;\n"
"}\n"
"\n"
"/*  Pages du formulaire */\n"
"QLabel.boite1{\n"
"background-color: #e7d2d9;\n"
"border-top: 2px solid #e7d2d9;\n"
"border-left: 2px solid #e7d2d9;\n"
"border-right: 2px solid #e7d2d9;\n"
"border-top-left-radius: 6px;\n"
"border-top-right-radius: 6px;\n"
"font-size: 20px;\n"
"text-align:center;\n"
"font: bold;\n"
"color: #ffffff;\n"
"}\n"
"QListView {\n"
"border-left: 2px solid #e7d2d9;\n"
"border-right: 2px solid #e7d2d9;\n"
"border-bottom: 2px solid #e7d2d9;\n"
"font-size: 10px;\n"
"border-bottom-left-radius: 6px;\n"
"border-bottom-right-radius: 6px;\n"
"}\n"
"/*  formulaire */\n"
"QScrollArea QWidget{\n"
"background-color: white;\n"
"}\n"
"\n"
"QLabel.texte01{\n"
"font-size: 11px;\n"
"}\n"
"QLabel.texte02{\n"
"font-size: 9px;\n"
"}\n"
"QLabel.code{\n"
"font-size: 12px;\n"
"font-weight : bold;\n"
"}\n"
""))
        Declaration.setLocale(QtCore.QLocale(QtCore.QLocale.French, QtCore.QLocale.France))
        self.gridLayout = QtGui.QGridLayout(Declaration)
        self.gridLayout.setObjectName(_fromUtf8("gridLayout"))
        self.verticalLayout = QtGui.QVBoxLayout()
        self.verticalLayout.setSpacing(0)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.label_8 = QtGui.QLabel(Declaration)
        self.label_8.setMinimumSize(QtCore.QSize(0, 27))
        self.label_8.setMaximumSize(QtCore.QSize(16777215, 27))
        self.label_8.setStyleSheet(_fromUtf8(""))
        self.label_8.setAlignment(QtCore.Qt.AlignCenter)
        self.label_8.setObjectName(_fromUtf8("label_8"))
        self.verticalLayout.addWidget(self.label_8)
        self.contents_widget = QtGui.QListWidget(Declaration)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.contents_widget.sizePolicy().hasHeightForWidth())
        self.contents_widget.setSizePolicy(sizePolicy)
        self.contents_widget.setMinimumSize(QtCore.QSize(200, 200))
        self.contents_widget.setMaximumSize(QtCore.QSize(200, 200))
        self.contents_widget.setObjectName(_fromUtf8("contents_widget"))
        self.verticalLayout.addWidget(self.contents_widget)
        spacerItem = QtGui.QSpacerItem(20, 10, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Fixed)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_2 = QtGui.QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.label_5 = QtGui.QLabel(Declaration)
        self.label_5.setMinimumSize(QtCore.QSize(108, 210))
        self.label_5.setMaximumSize(QtCore.QSize(108, 210))
        self.label_5.setText(_fromUtf8(""))
        self.label_5.setScaledContents(True)
        self.label_5.setAlignment(QtCore.Qt.AlignCenter)
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.horizontalLayout_2.addWidget(self.label_5)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        spacerItem1 = QtGui.QSpacerItem(20, 40, QtGui.QSizePolicy.Minimum, QtGui.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.buttonBox = QtGui.QDialogButtonBox(Declaration)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.verticalLayout.addWidget(self.buttonBox)
        self.gridLayout.addLayout(self.verticalLayout, 0, 0, 1, 1)
        self.verticalLayout_3 = QtGui.QVBoxLayout()
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setObjectName(_fromUtf8("verticalLayout_3"))
        self.frame = QtGui.QFrame(Declaration)
        self.frame.setMinimumSize(QtCore.QSize(0, 27))
        self.frame.setStyleSheet(_fromUtf8(""))
        self.frame.setFrameShape(QtGui.QFrame.StyledPanel)
        self.frame.setFrameShadow(QtGui.QFrame.Raised)
        self.frame.setObjectName(_fromUtf8("frame"))
        self.verticalLayout_2 = QtGui.QVBoxLayout(self.frame)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setMargin(0)
        self.verticalLayout_2.setObjectName(_fromUtf8("verticalLayout_2"))
        self.horizontalLayout = QtGui.QHBoxLayout()
        self.horizontalLayout.setSpacing(12)
        self.horizontalLayout.setContentsMargins(6, -1, 6, -1)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.label = QtGui.QLabel(self.frame)
        self.label.setObjectName(_fromUtf8("label"))
        self.horizontalLayout.addWidget(self.label)
        self.prev_btn = QtGui.QToolButton(self.frame)
        self.prev_btn.setArrowType(QtCore.Qt.LeftArrow)
        self.prev_btn.setObjectName(_fromUtf8("prev_btn"))
        self.horizontalLayout.addWidget(self.prev_btn)
        spacerItem2 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem2)
        self.label_10 = QtGui.QLabel(self.frame)
        self.label_10.setMinimumSize(QtCore.QSize(200, 27))
        self.label_10.setMaximumSize(QtCore.QSize(16777215, 27))
        self.label_10.setStyleSheet(_fromUtf8(""))
        self.label_10.setAlignment(QtCore.Qt.AlignCenter)
        self.label_10.setObjectName(_fromUtf8("label_10"))
        self.horizontalLayout.addWidget(self.label_10)
        spacerItem3 = QtGui.QSpacerItem(40, 20, QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem3)
        self.next_btn = QtGui.QToolButton(self.frame)
        self.next_btn.setArrowType(QtCore.Qt.RightArrow)
        self.next_btn.setObjectName(_fromUtf8("next_btn"))
        self.horizontalLayout.addWidget(self.next_btn)
        self.label_2 = QtGui.QLabel(self.frame)
        self.label_2.setObjectName(_fromUtf8("label_2"))
        self.horizontalLayout.addWidget(self.label_2)
        self.verticalLayout_2.addLayout(self.horizontalLayout)
        self.scrollArea = QtGui.QScrollArea(self.frame)
        self.scrollArea.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.scrollArea.setObjectName(_fromUtf8("scrollArea"))
        self.scrollAreaWidgetContents = QtGui.QWidget()
        self.scrollAreaWidgetContents.setGeometry(QtCore.QRect(0, 0, 749, 490))
        self.scrollAreaWidgetContents.setObjectName(_fromUtf8("scrollAreaWidgetContents"))
        self.scrollArea.setWidget(self.scrollAreaWidgetContents)
        self.verticalLayout_2.addWidget(self.scrollArea)
        self.verticalLayout_3.addWidget(self.frame)
        self.gridLayout.addLayout(self.verticalLayout_3, 0, 1, 1, 1)
        self.gridLayout.setColumnStretch(1, 1)

        self.retranslateUi(Declaration)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), Declaration.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), Declaration.reject)
        QtCore.QMetaObject.connectSlotsByName(Declaration)

    def retranslateUi(self, Declaration):
        Declaration.setWindowTitle(QtGui.QApplication.translate("Declaration", "Déclaration", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setText(QtGui.QApplication.translate("Declaration", "PAGES", None, QtGui.QApplication.UnicodeUTF8))
        self.label_8.setProperty("class", QtGui.QApplication.translate("Declaration", "boite1", None, QtGui.QApplication.UnicodeUTF8))
        self.label_5.setProperty("class", QtGui.QApplication.translate("Declaration", "sponsor", None, QtGui.QApplication.UnicodeUTF8))
        self.frame.setProperty("class", QtGui.QApplication.translate("Declaration", "top", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Declaration", "Précédent", None, QtGui.QApplication.UnicodeUTF8))
        self.prev_btn.setText(QtGui.QApplication.translate("Declaration", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setText(QtGui.QApplication.translate("Declaration", "FORMULAIRE", None, QtGui.QApplication.UnicodeUTF8))
        self.label_10.setProperty("class", QtGui.QApplication.translate("Declaration", "boite1", None, QtGui.QApplication.UnicodeUTF8))
        self.next_btn.setText(QtGui.QApplication.translate("Declaration", "...", None, QtGui.QApplication.UnicodeUTF8))
        self.label_2.setText(QtGui.QApplication.translate("Declaration", "Suivant", None, QtGui.QApplication.UnicodeUTF8))

import resources_rc
