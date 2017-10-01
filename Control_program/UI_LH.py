# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'UI_LH.ui'
#
# Created: Sun May 22 15:36:36 2016
#      by: PyQt4 UI code generator 4.10.4
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
        GNSSAzElWindow.resize(650, 690)
        self.verticalLayoutWidget = QtGui.QWidget(GNSSAzElWindow)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(20, 640,100, 24))
        self.verticalLayoutWidget.setObjectName(_fromUtf8("verticalLayoutWidget"))
        self.verticalLayout = QtGui.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setMargin(0)
        self.horizontalLayoutWidget = QtGui.QWidget(GNSSAzElWindow)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(20, 610, 320, 108))
        self.horizontalLayoutWidget.setObjectName(_fromUtf8("horizontalLayoutWidget"))
        self.horizontalLayouCheckBox = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayouCheckBox.setMargin(0)
        self.horizontalLayouCheckBox.setObjectName(_fromUtf8("horizontalLayoutCheckBox"))
        self.checkBoxGPS = QtGui.QCheckBox(self.horizontalLayoutWidget)
        self.checkBoxGPS.setObjectName(_fromUtf8("checkBoxGPS"))
        self.horizontalLayouCheckBox.addWidget(self.checkBoxGPS)
        self.checkBoxGALILEO = QtGui.QCheckBox(self.horizontalLayoutWidget)
        self.checkBoxGALILEO.setObjectName(_fromUtf8("checkBoxGALILEO"))
        self.horizontalLayouCheckBox.addWidget(self.checkBoxGALILEO)
        self.checkBoxGLONASS = QtGui.QCheckBox(self.horizontalLayoutWidget)
        self.checkBoxGLONASS.setObjectName(_fromUtf8("checkBoxGLONASS"))
        self.horizontalLayouCheckBox.addWidget(self.checkBoxGLONASS)
        self.checkBoxBEIDOU = QtGui.QCheckBox(self.horizontalLayoutWidget)
        self.checkBoxBEIDOU.setObjectName(_fromUtf8("checkBoxBEIDOU"))
        self.horizontalLayouCheckBox.addWidget(self.checkBoxBEIDOU)

        self.horizontalLayoutWidget = QtGui.QWidget(GNSSAzElWindow)
        self.horizontalLayoutWidget.setGeometry(QtCore.QRect(570, 640, 60, 40))
        self.horizontalLayoutWidget.setObjectName(_fromUtf8("horizontalLayoutWidget"))
        self.horizontalLayout = QtGui.QHBoxLayout(self.horizontalLayoutWidget)
        self.horizontalLayout.setMargin(0)
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
        self.btn_close = QtGui.QPushButton(self.horizontalLayoutWidget)
        self.btn_close.setObjectName(_fromUtf8("btn_close"))
        self.horizontalLayout.addWidget(self.btn_close)
        self.btn_close.setText(_translate("GNSSAzElWindow", "Close", None))

        self.retranslateUi(GNSSAzElWindow)
        QtCore.QMetaObject.connectSlotsByName(GNSSAzElWindow)

    def retranslateUi(self, GNSSAzElWindow):
        GNSSAzElWindow.setWindowTitle(_translate("GNSSAzElWindow", "GNSS Azimuth-Elevation View", None))
        self.checkBoxGPS.setText(_translate("GNSSAzElWindow", "GPS", None))
        self.checkBoxGLONASS.setText(_translate("GNSSAzElWindow", "GLONASS", None))
        self.checkBoxGALILEO.setText(_translate("GNSSAzElWindow", "GALILEO", None))
        self.checkBoxBEIDOU.setText(_translate("GNSSAzElWindow", "BEIDOU", None))
