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
#
# low-level serial communication with Grbl.
#
# Based in part on code by Will Welch, https://github.com/welch/shapeoko
# Original license:
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.

from PySide.QtCore import *
from GCodeAnalyzer import GCodeAnalyzer
import serial
import time
import glob
import re

import pycnc_config


def readConfigLine(line):
    # a config line is $key=value (comment)
    match = re.match("\$([0-9]+)\s*=\s*([0-9.]+).*", line)
    if match:
        return int(match.group(1)), float(match.group(2))
    return None, None


# minimal implementation of Grbl writer interface. Just echoes the commands
class GrblWriter(QObject):

    position_updated = Signal(object)

    def __init__(self):
        QObject.__init__(self)
        self.analyzer = GCodeAnalyzer(False)
        self.serial = None
        self.config = {}
        self.g0_feed = pycnc_config.G0_FEED
        self.waitAck = False
        self.storedPos = None

    # this will actually connect to Grbl
    def open(self):
        self.waitAck = False
        grbl_paths = glob.glob(pycnc_config.SERIAL_PATTERN)
        if not grbl_paths:
            return False # Device not existing

        try:
            self.serial = serial.Serial(grbl_paths[0], pycnc_config.BAUD, timeout=5, dsrdtr=True)
            self.serial.write("\r\n")
            time.sleep(2)  # wake up!
            self.serial.flushInput()
            self.load_config()
        except:
            # serial port could not be opened
            return False
        self.analyzer.Reset()
        self.analyzer.fastf = self.g0_feed
        # everything OK
        return True


    def reset(self):
        self.serial.close()
        self.position_updated.emit([0,0,0])
        return self.open()

    def read_response(self, until="ok"):
        """
            read lines from the grbl until the expected matching line appears
            (usually "ok"), or just the first line if until is None.
        """
        result = []

        while True:
            line = self.serial.readline().strip()
            if line.startswith("error:"):
                break

            result.append(line)
            if line == until or until == None:
                break
            time.sleep(0.1)

        return '\n'.join(result)

    def do_command(self, gcode, wait=False):
        """
            send the command to grbl, read the response and return it.
            if wait=True, wait for the stepper motion to complete before returning.
        """
        # self.waitAck = False # only for nonblocking commands, so it should be false, but if we run a nonblocking command, and then a blocking one, the blocking might catch the previous ok
        command = gcode.strip()
        if not command or command[0] == '(':
            return
        self.serial.write(command + '\n')
        response = self.read_response()
        if wait:
            self.wait_motion()

        self.analyzer.Analyze(command)
        self.position_updated.emit(self.analyzer.getPosition())

        return response

    def do_command_nonblock(self, gcode):
        # run a command but don't wait
        command = gcode.strip()
        if not command or command[0] == '(':
            return
        self.waitAck = True
        self.serial.write(command + '\n')
        self.analyzer.Analyze(command)
        self.position_updated.emit(self.analyzer.getPosition())

    def ack_received(self):
        if not self.waitAck:
            return True, None

        # there is no serial to be received, return false
        if not self.serial.inWaiting() > 0:
            return False, None

        line = self.serial.readline().strip()
        if line.startswith("error:"):
            self.waitAck = False
            return True, line

        if line == "ok":
            self.waitAck = False
            return True, line

        # something was received, but was not error or ok, so no ack
        return False, line

    def wait_motion(self):
        """
        force grbl to wait until all motion is complete.
        """
        #
        # the gcode dwell command as implemented by grbl includes a
        # stepper-motor sync prior to beginning the dwell countdown.
        # use it to force a pause-until-caught-up.
        self.do_command("G4 P0")


    def wait_motion_nonblock(self):
        self.do_command_nonblock("G4 P0")
        # self.motionWaiting = True
        # self.serial.flushInput()
        # self.serial.write("G4 P0\n")


    def load_config(self):
        # query GRBL for the configuration
        conf = self.do_command("$$")
        self.config = {}
        for confLine in conf.split("\n"):
            key,val = readConfigLine(confLine)
            if key is not None:
                self.config[key] = val

        try:
            self.g0_feed = self.config[110] # $110 in grbl is max x rate
        except:
            pass # if it's not there, it's ok

    def store_pos(self):
        self.storedPos={}
        self.storedPos['Position'] = self.analyzer.getPosition()
        self.storedPos['f'] = self.analyzer.f
        self.storedPos['relative'] = self.analyzer.relative
        self.storedPos['metric'] = self.analyzer.metric

    def resume_pos(self):
        # go back to the stored position
        safeZ = self.analyzer.maxZ
        xyz = self.storedPos['Position']
        self.do_command("G90") # go to abs positioning
        self.do_command("G21") # go to metric
        self.do_command("G0 Z%.4f" % safeZ) # move to safe Z
        self.do_command("G0 X%.4f Y%.4f" % (xyz[0], xyz[1])) # move to XY
        self.do_command("G1 Z%.4f F%.4f" % (xyz[2], self.storedPos['f'])) # move to Z using previous F

        # we are now in absolute metric: convert to relative/imperial if needed
        if self.storedPos['relative']:
            self.do_command("G91")

        if not self.storedPos['metric']:
            self.do_command("G20")
