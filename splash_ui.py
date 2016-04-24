# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'splash.ui'
#
# Created: Sun Apr 24 11:46:15 2016
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Splash(object):
    def setupUi(self, Splash):
        Splash.setObjectName("Splash")
        Splash.resize(480, 320)
        self.label = QtGui.QLabel(Splash)
        self.label.setGeometry(QtCore.QRect(0, 110, 480, 71))
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(20)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.AbortButton = QtGui.QPushButton(Splash)
        self.AbortButton.setGeometry(QtCore.QRect(154, 189, 181, 71))
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(27)
        font.setWeight(50)
        font.setBold(False)
        self.AbortButton.setFont(font)
        self.AbortButton.setObjectName("AbortButton")

        self.retranslateUi(Splash)
        QtCore.QMetaObject.connectSlotsByName(Splash)

    def retranslateUi(self, Splash):
        Splash.setWindowTitle(QtGui.QApplication.translate("Splash", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Splash", "Some text here", None, QtGui.QApplication.UnicodeUTF8))
        self.AbortButton.setText(QtGui.QApplication.translate("Splash", "Abort", None, QtGui.QApplication.UnicodeUTF8))

