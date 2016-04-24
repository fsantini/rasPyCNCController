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
from GCodeAnalyzer import GCodeAnalyzer
import time

# minimal implementation of Grbl writer interface. Just echoes the commands
class GrblWriterBasic(QObject):

    position_updated = Signal(object)

    def __init__(self):
        QObject.__init__(self)
        self.analyzer = GCodeAnalyzer()
        self.g0_feed = 5000
        self.config = {}

    # this will actually connect to Grbl
    def open(self):
        return True

    def reset(self):
        self.position_updated.emit([0,0,0])
        self.analyzer.Reset()

    def do_command(self, gcode, wait=False):
        print(gcode)
        self.analyzer.Analyze(gcode)
        self.position_updated.emit(self.analyzer.getPosition())
        time.sleep(0.1)

    def wait_motion(self):
        pass

    def do_command_nonblock(self, gcode):
        print gcode
        self.analyzer.Analyze(gcode)
        self.position_updated.emit(self.analyzer.getPosition())
        time.sleep(0.01)

    def ack_received(self):
        return True, None

    def wait_motion_nonblock(self):
        pass

    def load_config(self):
        pass

    def store_pos(self):
        self.storedPos = {}
        self.storedPos['Position'] = self.analyzer.getPosition()
        self.storedPos['f'] = self.analyzer.f
        self.storedPos['relative'] = self.analyzer.relative
        self.storedPos['metric'] = self.analyzer.metric

    def resume_pos(self):
        # go back to the stored position
        safeZ = self.analyzer.maxZ
        xyz = self.storedPos['Position']
        self.do_command("G90")  # go to abs positioning
        self.do_command("G21")  # go to metric
        self.do_command("G0 Z%.4f" % safeZ)  # move to safe Z
        self.do_command("G0 X%.4f Y%.4f" % (xyz[0], xyz[1]))  # move to XY
        self.do_command("G1 Z%.4f F%.4f" % (xyz[2], self.storedPos['f']))  # move to Z using previous F

        # we are now in absolute metric: convert to relative/imperial if needed
        if self.storedPos['relative']:
            self.do_command("G91")

        if not self.storedPos['metric']:
            self.do_command("G20")