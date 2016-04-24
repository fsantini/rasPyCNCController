# rasPyCNCController
# Copyright 2016 Francesco Santini <francesco.santini@gmail.com>
#
# This file is part of rasPyCNCController.
#
# rasPyCNCController is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# rasPyCNCController is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with rasPyCNCController.  If not, see <http://www.gnu.org/licenses/>.

import psutil
import sys
from filelist_ui import Ui_FileList
from PySide.QtGui import *
import os
import os.path
import re
import pycnc_config
from string_format import config_string_format


# see: https://stackoverflow.com/questions/2696733/set-bold-rows-in-a-qtreeview
class DirBoldDelegate(QStyledItemDelegate):
    def __init__(self, parent = None):
        QStyledItemDelegate.__init__(self, parent)
        self.boldIndexList = []

    def paint(self, painter, option, index):
        # decide here if item should be bold and set font weight to bold if needed
        if index.row() in self.boldIndexList:
            option.font.setWeight(QFont.Bold)
        QStyledItemDelegate.paint(self, painter, option, index)

class FileList(Ui_FileList, QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)

        # replace button text with config placeholders
        self.OKButton.setText(config_string_format(self.OKButton.text()))
        self.CancelButton.setText(config_string_format(self.CancelButton.text()))

        ## config params
        self.path=os.path.abspath(".")
        self.fileFilters = pycnc_config.GCODE_PATTERN #['.*']
        self.showHidden = False
        self.currentFile = ""



        # setup list models
        self.modelParts = QStandardItemModel(self.listView_left)
        self.listView_left.setModel(self.modelParts)

        self.modelFiles = QStandardItemModel(self.listView_right)
        self.listView_right.setModel(self.modelFiles)
        self.dirBoldDelegate = DirBoldDelegate(self)
        self.listView_right.setItemDelegate(self.dirBoldDelegate)

        # populate lists
        self.populateDevices()

        # connect signals
        self.listView_left.clicked.connect(lambda : self.partChanged())
        self.listView_right.clicked.connect(lambda: self.fileChanged())
        self.OKButton.clicked.connect(lambda : self.okClicked())
        self.CancelButton.clicked.connect(lambda : self.cancelClicked())
        self.populateFiles()


    # load partitions
    def populateDevices(self):
        parts = psutil.disk_partitions()
        self.modelParts.clear()
        self.parts = []

        for part in parts:
            item = QStandardItem(part.mountpoint)
            item.setCheckable(False)
            item.setEditable(False)
            self.modelParts.appendRow(item)
            self.parts.append(part.mountpoint)

    def fileChanged(self):
        selIndex = self.getSelFileIndex()
        self.currentFile = ""
        if selIndex == -1:
            return
        selFile = self.files[selIndex]

        # is a directory clicked upon? change path
        if os.path.isdir(os.path.abspath(selFile)):
            self.path = os.path.abspath(selFile)
            self.populateFiles()
        else:
            self.currentFile = os.path.abspath(selFile)

    # call this when a partition is changed to reload files
    def partChanged(self):
        selIndex = self.getSelPartIndex()
        if selIndex == -1: return
        selPart = self.parts[selIndex]
        self.path = os.path.abspath(selPart)
        self.populateFiles()

    # generic method to get the selected index of a listview
    def _getSelIndex(self, listView):
        sel = listView.selectionModel().selectedRows()
        if len(sel) == 0: return -1
        return sel[0].row()

    def _unselectView(self, listView):
        listView.selectionModel().clearSelection()

    def _selectIndex(self, listView, model, index):
        self._unselectView(listView)
        mIndex = model.index(index, 0)
        listView.selectionModel().select(mIndex, QItemSelectionModel.Select)
        listView.scrollTo(mIndex)


    def getSelFileIndex(self):
        return self._getSelIndex(self.listView_right)

    def unselectFiles(self):
        self._unselectView(self.listView_right)

    def selectFile(self, fileIndex):
        self._selectIndex(self.listView_right, self.modelFiles, fileIndex)

    def getSelPartIndex(self):
        return self._getSelIndex(self.listView_left)

    # clear selections in the UI
    def unselectParts(self):
        self._unselectView(self.listView_left)

    # select a specific partition in the UI
    def selectPart(self, partIndex):
        self._selectIndex(self.listView_left, self.modelParts, partIndex)

    # decides whether to add a file to the list depending on filename
    def acceptFile(self, f):
        accept = False
        for pattern in self.fileFilters:
            if re.match(pattern, f):
                accept = True

        return accept

    def populateFiles(self):
        dirs = []
        files = []
        self.dirBoldDelegate.boldIndexList = [0]
        dirs.append('..') # this is the first directory always
        for f in sorted(os.listdir(self.path)):
            fpath = os.path.join(self.path, f)
            if self.showHidden == False and f.startswith('.'): continue
            if os.path.isdir(os.path.abspath(fpath)):
                dirs.append(f)
            else:
                if self.acceptFile(f): # only add files corresponding to a certain filter
                    files.append(f)

        self.files = []
        # update view
        self.modelFiles.clear()
        curItemIndex = 1
        for d in dirs:
            item = QStandardItem(d)
            item.setCheckable(False)
            item.setEditable(False)
            #make dirs bold
            font = item.font()
            font.setBold(True)
            item.setFont(font)
            self.modelFiles.appendRow(item)
            self.dirBoldDelegate.boldIndexList.append(curItemIndex)
            curItemIndex += 1
            self.files.append(os.path.join(self.path, d))

        for f in files:
            item = QStandardItem(f)
            item.setCheckable(False)
            item.setEditable(False)
            # make dirs bold
            font = item.font()
            font.setBold(False)
            item.setFont(font)
            self.modelFiles.appendRow(item)
            self.files.append(os.path.join(self.path, f))

    def okClicked(self):
        print self.currentFile
        self.destroy()

    def cancelClicked(self):
        print "Cancelled"
        self.destroy()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FileList()
    window.show()
    sys.exit(app.exec_())
