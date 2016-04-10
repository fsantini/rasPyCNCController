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

from PySide.QtCore import QThread, Signal
import re
import sys
import time

def truncateGCode(gcode):
  def replace(match):
	match = match.group(2)
	return "." + match[0:4]

  pattern = re.compile(r"([.])([0-9]+)")
  return re.sub(pattern, replace, gcode)

class GCodeRunner(QThread):

    error_event = Signal(object)
    progress_event = Signal(object)
    stop_event = Signal()
    pause_event = Signal(object)
    end_event = Signal()


    def __init__(self):
        QThread.__init__(self)
        self.grblWriter = None
        self.gcode = None
        self.stopFlag = False
        self.pauseFlag = False
        self.currentLine = 0

    def setGrbl(self, grblWriter):
        self.grblWriter = grblWriter

    def setGcode(self, gcode):
        self.gcode = gcode
        self.currentLine = 0

    def togglePause(self):
        self.pauseFlag = not self.pauseFlag
        # emit an event if pause is toggled
        self.pause_event.emit(self.pauseFlag)

    def stop(self):
        self.stopFlag = True

    def run(self):
        totLines = len(self.gcode)

        if self.grblWriter == None or self.gcode == None: return
        self.pauseFlag = False
        self.stopFlag = False

        while (self.currentLine < totLines):

            if (self.stopFlag):
                self.grblWriter.reset()
                self.stop_event.emit()
                return

            ack, lineIn = self.grblWriter.ack_received()
            if not ack:
                time.sleep(0.01)
                continue

            # check for pause is after check for ack, so we are sure that GRBL is in sync
            if (self.pauseFlag):
                # idle loop during pause
                time.sleep(0.1)
                continue

            try:
                line = truncateGCode(self.gcode[self.currentLine])
                self.grblWriter.do_command_nonblock(line)
                self.currentLine += 1
                self.progress_event.emit(self.currentLine)
            except:
                e = sys.exc_info()[0]
                self.error_event.emit("%s" % e)

        # wait for the last ack
        while True:
            ack, lineIn = self.grblWriter.ack_received()
            if ack:
                break
            time.sleep(0.01)

        #self.grblWriter.wait_motion()
        self.grblWriter.wait_motion_nonblock()
        while not self.grblWriter.ack_received():
            if self.stopFlag:
                self.grblWriter.reset()
                self.stop_event.emit()
                return
            time.sleep(0.1)
        self.end_event.emit()

