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

from PySide.QtCore import *
from PySide.QtGui import *
from runWidget_ui import Ui_runWidget
from gcode.GCodeRunner import GCodeRunner
import os.path
from pyJoy.JoyEventGenerator import JoyEventGenerator
import time

class RunJoyEventGenerator(JoyEventGenerator):

    event_stop = Signal()
    event_pause = Signal()

    def __init__(self):
        JoyEventGenerator.__init__(self)

    # redefine what happens with a hat event
    def hatEvent(self, hEv):
       pass

    def btnEvent(self, bEv):
        # mapped buttons are 9 - Stop, 10 - Pause
        if bEv == 8:
            self.event_stop.emit()
        elif bEv == 9:
            self.event_pause.emit()

class RunWidget(Ui_runWidget, QWidget):

    error_event = Signal(object)
    stop_event = Signal()
    end_event = Signal()
    pause_event = Signal(object)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.setupUi(self)
        self.gcode = None
        self.times = None
        self.totalTime = None
        self.runner = None
        self.file = ""
        self.joy = RunJoyEventGenerator()
        self.PauseButton.clicked.connect(self.pause)
        self.joy.event_pause.connect(self.pause)
        self.initElements()
        self.running = False


    def initElements(self):
        self.setTime(0)
        self.estTimeProgress.setValue(0)
        self.PauseButton.setEnabled(False)
        self.PauseButton.setText("Pause")
        self.isPaused = False
        self.fileLabel.setText(os.path.basename(self.file))

    def setGrbl(self, grblWriter):
        self.grblWriter = grblWriter


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

    def runGCode(self, filename, gcode, times, totalTime, bbox):
        if self.grblWriter == None:
            self.error_event.emit("No Grbl writer")
            return

        self.file = filename
        self.gcode = gcode
        self.times = times
        self.totalTime = totalTime
        self.initElements()
        self.estTimeProgress.setMaximum(totalTime)
        self.setBBox(bbox)
        # instantiate GCodeRunner
        self.runner = GCodeRunner()
        self.runner.setGrbl(self.grblWriter)
        self.runner.progress_event.connect(self.setProgress)

        self.PauseButton.setEnabled(True)
        self.StopButton.clicked.connect(self.resetGrbl)
        self.joy.event_stop.connect(self.resetGrbl)

        # forward the events
        self.runner.error_event.connect(lambda err: self.error_event.emit(err))
        self.runner.end_event.connect(lambda : self.end_event.emit() )
        self.runner.stop_event.connect(lambda : self.stop_event.emit())
        self.runner.pause_event.connect(lambda pauseFlag: self.pause_event.emit(pauseFlag))

        self.runner.error_event.connect(lambda err: self.stopJoy())
        self.runner.pause_event.connect(lambda pauseFlag: self.stopJoy() if pauseFlag else None) # stop the joy on pause
        self.runner.end_event.connect(lambda : self.stopJoy())
        self.runner.stop_event.connect(lambda : self.stopJoy())

        self.runner.error_event.connect(lambda err: self.setRunning(False))
        self.runner.pause_event.connect(lambda pauseFlag: self.setRunning(not pauseFlag))
        self.runner.end_event.connect(lambda: self.setRunning(False))
        self.runner.stop_event.connect(lambda: self.setRunning(False))

        self.runner.setGcode(gcode)
        self.running = True
        self.runner.start()

    def setRunning(self, runStatus):
        self.running = runStatus

    def resetGrbl(self):
        self.runner.stop()

    def resume(self):
        self.isPaused = False
        self.PauseButton.setEnabled(True)
        # self.startJoy() # this called from the container?
        self.runner.resume()

    def cancelPause(self):
        self.runner.stop()
        self.resume()

    def pause(self):
        # we are already paused: do nothing
        if self.isPaused:
            return

        self.PauseButton.setEnabled(False)
        self.isPaused = True
        self.runner.pause()

    def setTime(self, timeSec):
        timeStr = self.formatTime(timeSec)
        self.estTimeProgress.setFormat(timeStr)
        self.estTimeProgress.setValue(self.estTimeProgress.maximum() - timeSec)

    def formatTime(self, timeSec):
        hours = int(timeSec / 3600)
        mins = int((timeSec - hours * 3600) / 60)
        secs = timeSec - hours * 3600 - mins * 60

        return ("%02d:%02d:%02d" % (hours, mins, secs))

    def setProgress(self, lineNo):
        if lineNo >= len(self.times):
            return
        self.setTime(self.totalTime - self.times[lineNo])

    def startJoy(self):
        time.sleep(0.5)
        self.joy.start()

    def stopJoy(self):
        self.joy.stop()
        time.sleep(0.05)
