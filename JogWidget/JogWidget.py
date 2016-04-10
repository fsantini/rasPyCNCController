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

import sys
import time

from PySide.QtCore import *
from PySide.QtGui import *

from jogWidget_ui import Ui_joyWidget
from pyJoy.JoyJogThread import JoyJogThread
from gcode.GCodeLoader import GCodeLoader
import os.path


class JogWidget(Ui_joyWidget, QWidget):

    run_event = Signal()
    load_event = Signal()
    error_event = Signal(object)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)

        self.RunButton.clicked.connect(self.runEvent)
        self.LoadButton.clicked.connect(self.loadEvent)

        self.joyJog = JoyJogThread()
        self.grblWriter = None
        # get the position from the writer - see below
        # self.joyJog.position_updated.connect(self.setPosition)
        self.joyJog.exit_event.connect(self.joyExitEvent)
        # propagate a GRBL error
        self.joyJog.error_event.connect(lambda err: self.error_event.emit(err))
        self.setPosition([0,0,0])
        self.disableControls()
        self.isFileLoaded = False

    def setGrbl(self, grblWriter):
        self.grblWriter = grblWriter
        self.grblWriter.position_updated.connect(self.setPosition)
        self.joyJog.setGrbl(grblWriter)

    def fileLoaded(self):
        self.isFileLoaded = True
        self.gcode = self.loader.gcode
        self.times = self.loader.times
        self.totalTime = self.loader.totalTime
        self.bBox = self.loader.bBox
        self.setBBox(self.loader.bBox)
        self.setEstTime(self.totalTime)
        self.RunButton.setEnabled(True)
        self.BBOxGroup.setEnabled(True)
        self.estTimeGroup.setEnabled(True)
        self.fileLabel.setText(os.path.basename(self.loader.file))

    def loadError(self, err):
        self.fileLabel.setText("Error loading: %s" % err)

    def loadFile(self, filename):
        self.file = filename
        self.isFileLoaded = False
        self.disableControls()
        self.loader = GCodeLoader()
        self.loader.g0_feed = self.grblWriter.g0_feed
        self.loader.load_finished.connect(self.fileLoaded)
        self.loader.load_error.connect(self.loadError)
        self.loader.load(filename)
        self.fileLabel.setText("Loading...")

    def displayError(self, err):
        if self.isFileLoaded:
            self.fileLabel.setText("Error: %s (%s)" % (err, self.file))
        else:
            self.fileLabel.setText("Error: %s" % err)

    def disableControls(self):
        self.RunButton.setEnabled(False)
        self.BBOxGroup.setEnabled(False)
        self.estTimeGroup.setEnabled(False)
        self.setBBox(None)
        self.setEstTime(None)

    def setBBox(self, BBox):
        if BBox == None:
            self.xMaxBBoxTxt.setText("")
            self.yMaxBBoxTxt.setText("")
            self.zMaxBBoxTxt.setText("")

            self.xMinBBoxTxt.setText("")
            self.yMinBBoxTxt.setText("")
            self.zMinBBoxTxt.setText("")
            return

        self.xMinBBoxTxt.setText("%.1f" % BBox[0][0])
        self.yMinBBoxTxt.setText("%.1f" % BBox[0][1])
        self.zMinBBoxTxt.setText("%.1f" % BBox[0][2])

        self.xMaxBBoxTxt.setText("%.1f" % BBox[1][0])
        self.yMaxBBoxTxt.setText("%.1f" % BBox[1][1])
        self.zMaxBBoxTxt.setText("%.1f" % BBox[1][2])

    def setEstTime(self, timeSec):
        if timeSec == None:
            timeSec = 0
        hours = int(timeSec / 3600)
        mins = int((timeSec - hours*3600)/60)
        secs = timeSec - hours*3600 - mins*60

        self.estTimeTxt.setText("%02d:%02d:%02d" % (hours, mins, secs))

    def startJoy(self):
        time.sleep(0.5)
        self.joyJog.start()

    def stopJoy(self):
        self.joyJog.stop()
        time.sleep(0.1)

    def setPosition(self, posXYZ):
        self.xPosTxt.setText("%.1f" % posXYZ[0])
        self.yPosTxt.setText("%.1f" % posXYZ[1])
        self.zPosTxt.setText("%.1f" % posXYZ[2])

    def runEvent(self):
        self.stopJoy()
        self.run_event.emit()

    def loadEvent(self):
        self.stopJoy()
        self.load_event.emit()

    def joyExitEvent(self, exitCondition):
        # joy is stopped now!
        if exitCondition == True:
            # Run was pressed
            if self.RunButton.isEnabled():
                self.runEvent()
            else:
                #runbutton is not enabled: restart the joy
                # give sime time to the thread to exit and then restart it
                time.sleep(0.1)
                self.startJoy()
        else:
            self.loadEvent()

class GrblWriter_debug:
    def do_command(self, cmd, wait = False):
        print(cmd)
        time.sleep(0.1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    grbl = GrblWriter_debug()
    window = JogWidget(grbl)
    window.destroyed.connect(window.stopJoy)
    window.show()
    sys.exit(app.exec_())