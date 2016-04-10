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

from PySide import QtCore
from GCodeAnalyzer import GCodeAnalyzer
import sys
import pycnc_config

class GCodeLoader(QtCore.QThread):

    load_finished = QtCore.Signal()
    load_error = QtCore.Signal(object)

    def __init__(self):
        QtCore.QThread.__init__(self)

        self.file = None
        self.gcode = None
        self.times = None
        self.bBox = None
        self.loaded = False
        self.totalTime = 0
        self.busy = False
        self.g0_feed = pycnc_config.G0_FEED

    def run(self):
        self.loaded = False
        self.gcode = []
        self.times = []
        self.bBox = None
        self.totalTime = 0
        self.busy = True

        analyzer = GCodeAnalyzer()
        analyzer.fastf = self.g0_feed

        try:
            with open(self.file) as f:
                for line in f:
                    analyzer.Analyze(line)
                    self.gcode.append(line)
                    self.times.append(analyzer.getTravelTime()*60) # time returned is in minutes: convert to seconds
        except:
            self.busy = False
            e = sys.exc_info()[0]
            self.load_error.emit("%s" % e)
            return

        self.busy = False
        self.loaded = True
        self.totalTime = self.times[-1]
        self.bBox = analyzer.getBoundingBox()
        self.load_finished.emit()

    def load(self, file):
        self.file = file
        self.start()






