# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'splash_expand.ui'
#
# Created: Fri Mar  2 20:15:46 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_Splash(object):
    def setupUi(self, Splash):
        Splash.setObjectName("Splash")
        Splash.resize(480, 320)
        self.verticalLayout = QtGui.QVBoxLayout(Splash)
        self.verticalLayout.setContentsMargins(-1, 20, -1, 20)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtGui.QLabel(Splash)
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(20)
        self.label.setFont(font)
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.AbortButton = QtGui.QPushButton(Splash)
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(27)
        font.setWeight(50)
        font.setBold(False)
        self.AbortButton.setFont(font)
        self.AbortButton.setObjectName("AbortButton")
        self.verticalLayout.addWidget(self.AbortButton)

        self.retranslateUi(Splash)
        QtCore.QMetaObject.connectSlotsByName(Splash)

    def retranslateUi(self, Splash):
        Splash.setWindowTitle(QtGui.QApplication.translate("Splash", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.label.setText(QtGui.QApplication.translate("Splash", "Some text here", None, QtGui.QApplication.UnicodeUTF8))
        self.AbortButton.setText(QtGui.QApplication.translate("Splash", "Abort", None, QtGui.QApplication.UnicodeUTF8))

