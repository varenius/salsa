# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_LH.ui'
#
# Created by: PyQt4 UI code generator 4.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_GNSSAzElWindow(object):
    def setupUi(self, GNSSAzElWindow):
        GNSSAzElWindow.setObjectName(_fromUtf8("GNSSAzElWindow"))
        GNSSAzElWindow.resize(650, 650)
        self.centralwidget = QtGui.QWidget(GNSSAzElWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.horizontalLayoutWidget = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(550, 0, 91, 31))
        self.horizontalLayoutWidget.setObjectName(_fromUtf8("horizontalLayoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btn_close = QtGui.QPushButton(self.horizontalLayoutWidget)
        self.btn_close.setObjectName(_fromUtf8("btn_close"))
        self.horizontalLayout.addWidget(self.btn_close)
        self.horizontalLayoutWidget_2 = QtGui.QWidget(self.centralwidget)
        self.horizontalLayoutWidget_2.setGeometry(QtCore.QRect(190, 0, 351, 24))
        self.horizontalLayoutWidget_2.setObjectName(_fromUtf8("horizontalLayoutWidget_2"))
        self.horizontalLayout_2 = QtGui.QHBoxLayout(self.horizontalLayoutWidget_2)
        self.horizontalLayout_2.setSizeConstraint(QtGui.QLayout.SetFixedSize)
        self.horizontalLayout_2.setMargin(0)
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2"))
        self.checkBoxGPS = QtGui.QCheckBox(self.horizontalLayoutWidget_2)
        self.checkBoxGPS.setAcceptDrops(False)
        self.checkBoxGPS.setChecked(True)
        self.checkBoxGPS.setObjectName(_fromUtf8("checkBoxGPS"))
        self.horizontalLayout_2.addWidget(self.checkBoxGPS)
        self.checkBoxGLONASS = QtGui.QCheckBox(self.horizontalLayoutWidget_2)
        self.checkBoxGLONASS.setChecked(True)
        self.checkBoxGLONASS.setObjectName(_fromUtf8("checkBoxGLONASS"))
        self.horizontalLayout_2.addWidget(self.checkBoxGLONASS)
        self.checkBoxGALILEO = QtGui.QCheckBox(self.horizontalLayoutWidget_2)
        self.checkBoxGALILEO.setChecked(True)
        self.checkBoxGALILEO.setObjectName(_fromUtf8("checkBoxGALILEO"))
        self.horizontalLayout_2.addWidget(self.checkBoxGALILEO)
        self.checkBoxBEIDOU = QtGui.QCheckBox(self.horizontalLayoutWidget_2)
        self.checkBoxBEIDOU.setChecked(True)
        self.checkBoxBEIDOU.setObjectName(_fromUtf8("checkBoxBEIDOU"))
        self.horizontalLayout_2.addWidget(self.checkBoxBEIDOU)
        GNSSAzElWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtGui.QMenuBar(GNSSAzElWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 650, 25))
        self.menubar.setObjectName(_fromUtf8("menubar"))
        self.file_menu = QtGui.QMenu(self.menubar)
        self.file_menu.setObjectName(_fromUtf8("file_menu"))
        self.help_menu = QtGui.QMenu(self.menubar)
        self.help_menu.setObjectName(_fromUtf8("help_menu"))
        GNSSAzElWindow.setMenuBar(self.menubar)
        self.statusBar = QtGui.QStatusBar(GNSSAzElWindow)
        self.statusBar.setObjectName(_fromUtf8("statusBar"))
        GNSSAzElWindow.setStatusBar(self.statusBar)
        self.file_menu.addSeparator()
        self.menubar.addAction(self.file_menu.menuAction())
        self.menubar.addAction(self.help_menu.menuAction())

        self.retranslateUi(GNSSAzElWindow)
        QtCore.QMetaObject.connectSlotsByName(GNSSAzElWindow)

    def retranslateUi(self, GNSSAzElWindow):
        GNSSAzElWindow.setWindowTitle(_translate("GNSSAzElWindow", "GNSS Azimuth-Elevation View", None))
        self.btn_close.setText(_translate("GNSSAzElWindow", "Close", None))
        self.checkBoxGPS.setText(_translate("GNSSAzElWindow", "GPS", None))
        self.checkBoxGLONASS.setText(_translate("GNSSAzElWindow", "GLONASS", None))
        self.checkBoxGALILEO.setText(_translate("GNSSAzElWindow", "GALILEO", None))
        self.checkBoxBEIDOU.setText(_translate("GNSSAzElWindow", "BEIDOU", None))
        self.file_menu.setTitle(_translate("GNSSAzElWindow", "File", None))
        self.help_menu.setTitle(_translate("GNSSAzElWindow", "Help", None))

