# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'pyFileList/filelist_expand.ui'
#
# Created: Fri Mar  2 20:15:46 2018
#      by: pyside-uic 0.2.15 running on PySide 1.2.2
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore, QtGui

class Ui_FileList(object):
    def setupUi(self, FileList):
        FileList.setObjectName("FileList")
        FileList.resize(480, 320)
        self.gridLayout = QtGui.QGridLayout(FileList)
        self.gridLayout.setObjectName("gridLayout")
        self.widget = QtGui.QWidget(FileList)
        self.widget.setObjectName("widget")
        self.horizontalLayout = QtGui.QHBoxLayout(self.widget)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listView_left = QtGui.QListView(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(1)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listView_left.sizePolicy().hasHeightForWidth())
        self.listView_left.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setWeight(75)
        font.setBold(True)
        self.listView_left.setFont(font)
        self.listView_left.setObjectName("listView_left")
        self.horizontalLayout.addWidget(self.listView_left)
        self.listView_right = QtGui.QListView(self.widget)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(2)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listView_right.sizePolicy().hasHeightForWidth())
        self.listView_right.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(16)
        font.setWeight(75)
        font.setBold(True)
        self.listView_right.setFont(font)
        self.listView_right.setObjectName("listView_right")
        self.horizontalLayout.addWidget(self.listView_right)
        self.gridLayout.addWidget(self.widget, 0, 0, 1, 2)
        self.OKButton = QtGui.QPushButton(FileList)
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(27)
        font.setWeight(75)
        font.setBold(True)
        self.OKButton.setFont(font)
        self.OKButton.setObjectName("OKButton")
        self.gridLayout.addWidget(self.OKButton, 1, 0, 1, 1)
        self.CancelButton = QtGui.QPushButton(FileList)
        font = QtGui.QFont()
        font.setFamily("FreeSans")
        font.setPointSize(27)
        font.setWeight(75)
        font.setBold(True)
        self.CancelButton.setFont(font)
        self.CancelButton.setObjectName("CancelButton")
        self.gridLayout.addWidget(self.CancelButton, 1, 1, 1, 1)

        self.retranslateUi(FileList)
        QtCore.QMetaObject.connectSlotsByName(FileList)

    def retranslateUi(self, FileList):
        FileList.setWindowTitle(QtGui.QApplication.translate("FileList", "Form", None, QtGui.QApplication.UnicodeUTF8))
        self.OKButton.setText(QtGui.QApplication.translate("FileList", "OK", None, QtGui.QApplication.UnicodeUTF8))
        self.CancelButton.setText(QtGui.QApplication.translate("FileList", "Cancel", None, QtGui.QApplication.UnicodeUTF8))

