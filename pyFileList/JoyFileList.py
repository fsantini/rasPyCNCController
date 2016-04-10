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

import time

from pyFileList.filelist import FileList
from pyJoy.JoyEventGenerator import JoyEventGenerator
import sys
import PySide.QtGui
import PySide.QtCore
import pycnc_config

class JoyFileListEventGen(JoyEventGenerator):

    event_right = PySide.QtCore.Signal()
    event_left = PySide.QtCore.Signal()
    event_up = PySide.QtCore.Signal()
    event_down = PySide.QtCore.Signal()

    event_select = PySide.QtCore.Signal()
    event_ok = PySide.QtCore.Signal()
    event_cancel = PySide.QtCore.Signal()

    def __init__(self):
        JoyEventGenerator.__init__(self)

    # redefine what happens with a hat event
    def hatEvent(self, hEv):
        # hat events are: 0-Right 1-Left 2-Up 3-Down
        if hEv == pycnc_config.HAT_RIGHT:
            self.event_right.emit()
        elif hEv == pycnc_config.HAT_LEFT:
            self.event_left.emit()
        elif hEv == pycnc_config.HAT_UP:
            self.event_up.emit()
        elif hEv == pycnc_config.HAT_DOWN:
            self.event_down.emit()

    def btnEvent(self, bEv):
        # mapped buttons are 1 - select, 9 - Ok, 10 - Cancel
        if bEv == pycnc_config.BTN_SELECT:
            self.event_select.emit()
        elif bEv == pycnc_config.BTN_OK:
            self.event_ok.emit()
        elif bEv == pycnc_config.BTN_CANCEL:
            self.event_cancel.emit()




class JoyFileList(FileList):

    ok_clicked = PySide.QtCore.Signal(object)
    cancel_clicked = PySide.QtCore.Signal(object)

    def __init__(self, parent=None):
        FileList.__init__(self,parent)
        self.joyEventGen = JoyFileListEventGen()

        self.joyEventGen.event_ok.connect(self.okClicked)
        self.joyEventGen.event_cancel.connect(self.cancelClicked)
        self.joyEventGen.event_select.connect(self.event_select)
        self.joyEventGen.event_right.connect(self.toggleView)
        self.joyEventGen.event_left.connect(self.toggleView)
        self.joyEventGen.event_up.connect(self.event_up)
        self.joyEventGen.event_down.connect(self.event_down)

        self.destroyed.connect(self.joyEventGen.stop)

        self.joyEventGen.start()

        self.currentView = 'FileView'
        self.lastSelPart = 0
        self.lastSelFile = 0
        self.selectFile(0)

    def toggleView(self):
        if self.currentView == 'FileView':
            # move to partition view
            self.lastSelFile = self.getSelFileIndex()
            if self.lastSelFile < 0: self.lastSelFile = 0
            self.unselectFiles()
            self.currentView = 'PartView'
            self.selectPart(self.lastSelPart)
        else:
            self.lastSelPart = self.getSelPartIndex()
            if self.lastSelPart < 0: self.lastSelPart = 0
            self.unselectParts()
            self.currentView = 'FileView'
            self.selectFile(self.lastSelFile)

    def event_up(self):
        if self.currentView == 'FileView':
            selFile = self.getSelFileIndex()
            selFile -= 1 # select the previous file in the list
            if selFile < 0: selFile = len(self.files)-1
            self.selectFile(selFile)
        else:
            selPart = self.getSelPartIndex()
            selPart -= 1
            if selPart < 0: selPart = len(self.parts)-1
            self.selectPart(selPart)

    def event_down(self):
        if self.currentView == 'FileView':
            selFile = self.getSelFileIndex()
            selFile += 1  # select the previous file in the list
            if selFile >= len(self.files): selFile = 0
            self.selectFile(selFile)
        else:
            selPart = self.getSelPartIndex()
            selPart += 1
            if selPart >= len(self.parts): selPart = 0
            self.selectPart(selPart)

    def populateFiles(self):
        # whenever we are populating the files, the last file selection is erased
        self.lastSelFile = 0
        FileList.populateFiles(self)

    def event_select(self):
        if self.currentView == 'FileView':
            self.fileChanged()
        else:
            self.partChanged()


    def startJoy(self):
        self.joyEventGen.start()

    def stopJoy(self):
        self.joyEventGen.stop()
        time.sleep(0.1)

    def okClicked(self):
        self.stopJoy()
        self.fileChanged()
        self.ok_clicked.emit(self.currentFile)

    def cancelClicked(self):
        self.stopJoy()
        self.fileChanged()
        self.cancel_clicked.emit(self.currentFile)

if __name__ == "__main__":
    app = PySide.QtGui.QApplication(sys.argv)
    window = JoyFileList()
    window.cancel_clicked.connect(window.stopEventGen)
    window.cancel_clicked.connect(lambda : window.destroy())
    window.ok_clicked.connect(window.stopEventGen)
    window.ok_clicked.connect(lambda : window.destroy())
    window.show()
    app.exec_()