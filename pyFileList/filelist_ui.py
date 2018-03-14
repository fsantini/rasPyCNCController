# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pyFileList/filelist.ui'
#
# Created: Wed Mar 14 07:27:30 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_FileList(object):
    def setupUi(self, FileList):
        FileList.setObjectName("FileList")
        FileList.resize(480, 321)
        self.listView_right = QtGui.QListView(FileList)
        self.listView_right.setGeometry(QtCore.QRect(150, 10, 321, 236))
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setWeight(75)
        font.setBold(True)
        self.listView_right.setFont(font)
        self.listView_right.setObjectName("listView_right")
        self.listView_left = QtGui.QListView(FileList)
        self.listView_left.setGeometry(QtCore.QRect(0, 10, 141, 236))
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setWeight(75)
        font.setBold(True)
        self.listView_left.setFont(font)
        self.listView_left.setObjectName("listView_left")
        self.OKButton = QtGui.QPushButton(FileList)
        self.OKButton.setGeometry(QtCore.QRect(0, 255, 231, 61))
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(27)
        font.setWeight(75)
        font.setBold(True)
        self.OKButton.setFont(font)
        self.OKButton.setObjectName("OKButton")
        self.CancelButton = QtGui.QPushButton(FileList)
        self.CancelButton.setGeometry(QtCore.QRect(240, 255, 231, 61))
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(27)
        font.setWeight(75)
        font.setBold(True)
        self.CancelButton.setFont(font)
        self.CancelButton.setObjectName("CancelButton")

        self.retranslateUi(FileList)
        QtCore.QMetaObject.connectSlotsByName(FileList)

    def retranslateUi(self, FileList):
        FileList.setWindowTitle(QtGui.QApplication.translate("FileList", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.OKButton.setText(QtGui.QApplication.translate("FileList", "OK (%BTN_OK+1%)", None, QtGui.QApplication.UnicodeUTF8))
        self.CancelButton.setText(QtGui.QApplication.translate("FileList", "Cancel (%BTN_CANCEL+1%)", None, QtGui.QApplication.UnicodeUTF8))

