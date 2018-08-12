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
import sys
import pycnc_config
import math

# run commands in a thread, so we can refuse or accept events while machine is busy
class JogThread(QThread):

    error_event = Signal(object)

    def __init__(self):
        QThread.__init__(self)
        self.cmd = ""
        self.grblWriter = None
        self.busy = False

    def run(self):
        if self.cmd == "" or self.grblWriter is None:
            return

        self.busy = True

        try:
            self.grblWriter.do_command(self.cmd, self.cncWait)
        except:
            self.busy = False
            e = sys.exc_info()[0]
            self.error_event.emit(e)

        self.grblWriter.update_position()

        self.cmd = ""
        self.busy = False

    def do_command(self, cmd, cncWait = False):
        self.cmd = cmd
        self.cncWait = cncWait
        self.start()


class JogHelper(QObject):

    error_event = Signal(object)

    def __init__(self, grbl = None):
        QObject.__init__(self)
        self.busy = False
        self.grblWriter = grbl
        self.jogThread = JogThread()
        self.jogThread.grblWriter = self.grblWriter
        self.jogThread.error_event.connect(lambda e: self.error_event.emit(e))
        self.cncWait = False

    def setGrbl(self, grbl):
        self.grblWriter = grbl
        self.jogThread.grblWriter = self.grblWriter

    def run_command(self, cmd, cncWait = False):
        if self.grblWriter is None or self.isBusy():
            return

        self.jogThread.do_command(cmd, cncWait)

    def waitThread(self):
        self.jogThread.wait()

    def isBusy(self):
        return self.jogThread.busy

    def relative_move(self, xyz, feed = None):
        if self.grblWriter is None: return

        if feed is None or feed < 0:
            cmd = "G0 X%.1f Y%.1f Z%.1f" % ( xyz[0], xyz[1], xyz[2])
        else:
            cmd = "G1 X%.1f Y%.1f Z%.1f F%d" % (xyz[0], xyz[1], xyz[2], feed)

        # if grbl is absolute, make relative
        if not self.grblWriter.analyzer.relative:
            self.run_command("G91")
            self.waitThread()

        if not self.grblWriter.analyzer.metric:
            self.run_command("G21")
            self.waitThread()

        self.run_command(cmd, True)

    def absolute_move(self, xyz, feed = None):
        if self.grblWriter is None: return

        if feed is None or feed < 0:
            cmd = "G0 X%.1f Y%.1f Z%.1f" % ( xyz[0], xyz[1], xyz[2])
        else:
            cmd = "G1 X%.1f Y%.1f Z%.1f F%d" % (xyz[0], xyz[1], xyz[2], feed)

        # if grbl is relative, make absolute
        if self.grblWriter.analyzer.relative:
            self.run_command("G90")
            self.waitThread()

        if not self.grblWriter.analyzer.metric:
            self.run_command("G21")
            self.waitThread()

        self.run_command(cmd, True)

    def home_update(self, xyz):
        if self.grblWriter is None: return
        cmd = "G10 P0 L20"
        if xyz[0] is not None:
            cmd += " X%.1f" % xyz[0]
        if xyz[1] is not None:
            cmd += " Y%.1f" % xyz[1]
        if xyz[2] is not None:
            cmd += " Z%.1f" % xyz[2]

        self.run_command(cmd)


class JogHelper1_1(JogHelper):

    def __init__(self):
        JogHelper.__init__(self)

    def relative_move(self, xyz, feed = None):
        print "Relative move received"
        if self.grblWriter is None: return

        # this is a jog stop
        if all([pos == 0 for pos in xyz]):
            print "Cancelling jog"
            self.grblWriter.cancelJog()
            self.grblWriter.wait_motion()
            self.grblWriter.update_position()
            return

        travelDistance = pycnc_config.BTN_REPEAT * float(feed)/60/1000 # distance to travel in the space of a btn_repeat

        plannedDistance = math.sqrt(xyz[0]**2 + xyz[1]**2 + xyz[2]**2)

        factor = travelDistance/plannedDistance

        cmd = "$J=G91 X%.1f Y%.1f Z%.1f F%d" % (xyz[0]*factor, xyz[1]*factor, xyz[2]*factor, feed)

        self.run_command(cmd, False)
