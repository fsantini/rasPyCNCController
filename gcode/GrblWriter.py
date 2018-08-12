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
from PySide.QtGui import QApplication, QMessageBox
from GCodeAnalyzer import GCodeAnalyzer
import serial
import time
import glob
import re
import math
from bisect import bisect_left, bisect_right
import types

import pycnc_config
from gcode.GrblErrors import GrblErrorDict


def suppressGCode(gcodeLine, toSuppress):
    gcodefinder = re.compile(toSuppress + '(?![0-9.])[^MG]*', re.I) # suppress M6 but not M66, even when it's M6G0, for example
    return gcodefinder.sub('', gcodeLine)

def suppressAllInvalidGCodes(gcodeline):
    for gcode in pycnc_config.SUPPRESS_GCODE:
        gcodeline = suppressGCode(gcodeline, gcode)
    return gcodeline

def showGrblErrorMessageBox(widget, lnum, line, err):
    message = "Error in GCode at line\n#%d: %s\n%s" % (lnum + 1, line.strip(), err.strip())
    m = re.search('error:\s*([0-9]+)', err)
    if m is not None:
        errno = int(m.group(1))
        if errno in GrblErrorDict:
            errmsg = GrblErrorDict[errno]
            message += '\n' + errmsg
    res = QMessageBox.critical(widget, "GCode error", message, QMessageBox.Abort | QMessageBox.Ignore)
    if res == QMessageBox.Ignore:
        return True
    else:
        return False

def redefineSerialRW(serialInstance):
    oldWrite = serialInstance.write

    def newWrite(self, data):
        print "Serial TX:", data.strip()
        oldWrite(data)

    serialInstance.write = types.MethodType(newWrite, serialInstance)

    oldReadline = serialInstance.readline

    def newReadline(self):
        data = oldReadline()
        print "Serial RX:", data.strip()
        return data

    serialInstance.readline = types.MethodType(newReadline, serialInstance)

def readConfigLine(line):
    # a config line is $key=value (comment)
    match = re.match("\$([0-9]+)\s*=\s*([0-9.]+).*", line)
    if match:
        return int(match.group(1)), float(match.group(2))
    return None, None

# class to compensate for Z offsets after a grid probe
class ZCompensation:

    def __init__(self, xRangeOrSize, yRangeOrSize, spacing):
        # predefines the grid. Inputs can be ranges (tuple) or sizes
        try:
            self.xrange = (xRangeOrSize[0], xRangeOrSize[1])
        except:
            # it must be a number, not a range
            self.xrange = (0.0, float(xRangeOrSize))

        try:
            self.yrange = (yRangeOrSize[0], yRangeOrSize[1])
        except:
            # it must be a number, not a range
            self.yrange = (0.0, float(yRangeOrSize))

        self.spacing = spacing

        if self.xrange[0] > self.xrange[1]: self.xrange = (self.xrange[1], self.xrange[0])
        if self.yrange[0] > self.yrange[1]: self.yrange = (self.yrange[1], self.yrange[0])

        self.nPointsX = int(math.ceil((self.xrange[1] - self.xrange[0]) / float(spacing)))+1
        self.nPointsY = int(math.ceil((self.yrange[1] - self.yrange[0]) / float(spacing)))+1

        print "Ranges: ", self.xrange, self.yrange

        self.xPoints = [(i*spacing + self.xrange[0]) for i in range(self.nPointsX)]
        self.yPoints = [(i*spacing + self.yrange[0]) for i in range(self.nPointsY)]

        print "Points X:", self.xPoints
        print "Points Y:", self.yPoints

        self.zValues = [[None for y in range(self.nPointsY)] for x in range(self.nPointsX)]

        # construct point list
        direction = +1
        self.probePointList = []
        self.probePointIndices = []
        for yInd in range(len(self.yPoints)):
            if direction == 1:
                xIter = range(len(self.xPoints))
            else:
                xIter = range(len(self.xPoints)-1, -1, -1)
            for xInd in xIter:
                self.probePointList.append((self.xPoints[xInd],self.yPoints[yInd]))
                self.probePointIndices.append((xInd,yInd))
            direction = -direction


    def getProbePoints(self):
        # returns a list of all the X,Y coordinates to probe
        return self.probePointList

    def setZValue(self, index, z, zOffset = 0):
        # sets a z value
        print "Setting Z(",self.probePointIndices[index][0],self.probePointIndices[index][1], "):", z+zOffset
        self.zValues[self.probePointIndices[index][0]][self.probePointIndices[index][1]] = z + zOffset

    def isValid(self):
        # check if all the values have been filled
        for zVec in self.zValues:
            if any(zVec is None):
                return False
        return True

    def _findInterpolationIndices(self, val, vec):
        #print "Finding ", val, " in ", vec
        if val <= vec[0]:
            weights = (1,0)
            indices = (0,0)
            return indices, weights
        if val >= vec[-1]:
            weights = (1,0)
            indices = (len(vec)-1, len(vec)-1)
            return indices, weights

        indexAfter = bisect_right(vec, val)
        indexBefore = indexAfter - 1
        #print "Bisect returned ", indexAfter
        weightBefore = (vec[indexAfter] - val)/(vec[indexAfter] - vec[indexBefore]) # the further the point is from the index before, the higher the weight
        weightAfter = 1.0 - weightBefore
        weights = (weightBefore, weightAfter)
        indices = (indexBefore, indexAfter)
        return indices, weights


    def getZValue(self, x, y):
        # this is where the magic happens: return an interpolated ZValue
        # find X
        #print "Getting Z value"
        xInd, xWeight = self._findInterpolationIndices(x, self.xPoints)
        #print "XInd,weight: ", xInd, xWeight
        yInd, yWeight = self._findInterpolationIndices(y, self.yPoints)
        #print "YInd,weight: ", yInd, yWeight
        z = (self.zValues[xInd[0]][yInd[0]]*xWeight[0]*yWeight[0] +
            self.zValues[xInd[0]][yInd[1]] * xWeight[0] * yWeight[1] +
            self.zValues[xInd[1]][yInd[0]] * xWeight[1] * yWeight[0] +
            self.zValues[xInd[1]][yInd[1]] * xWeight[1] * yWeight[1])

        return z



class GrblWriter(QObject):

    position_updated = Signal(object)
    probe_error = Signal()
    grbl_error = Signal(object)

    def __init__(self):
        QObject.__init__(self)
        self.analyzer = GCodeAnalyzer(False)
        self.serial = None
        self.config = {}
        self.g0_feed = pycnc_config.G0_FEED
        self.waitAck = 0
        self.storedPos = None
        self.zCompensation = None
        self.doZCompensation = False
        self.restoreWorkCoords = False
        self.checkMode = False
        self.resetting = False

    # this will actually connect to Grbl
    def open(self):
        self.waitAck = 0
        grbl_paths = glob.glob(pycnc_config.SERIAL_PATTERN)
        if not grbl_paths:
            return False # Device not existing

        self.checkMode = False

        try:
            self.serial = serial.Serial(grbl_paths[0], pycnc_config.BAUD, timeout=5, dsrdtr=True)
            if pycnc_config.SERIAL_DEBUG:
                redefineSerialRW(self.serial) # this is to debug communication!
            self.serial.flushInput()
            time.sleep(0.1)
            self.serial.write("\r\n")
            time.sleep(0.1)
            self.serial.write("\x18")
            time.sleep(0.1)
            grblLine = self.serial.readline()
            while 'Grbl' not in grblLine:
                grblLine = self.serial.readline()
                time.sleep(0.1)
            time.sleep(0.5)
            self.serial.flushInput()
            self.load_config(grblLine)
        except:
            # serial port could not be opened
            return False

        if self.config[22] == 1: # homing is enabled. A homing cycle needs to be performed.
            self.do_homing()
        else:
            self.analyzer.Reset()
            self.analyzer.fastf = self.g0_feed
        # everything OK
        return True

    def do_homing(self):
        res = QMessageBox.information(None, "Homing", "Press OK to start the homing cycle", QMessageBox.Ok)
        if res != QMessageBox.Ok:
            return

        oldMachineCoords = self.analyzer.getMachineXYZ()
        oldWorkCoords = self.analyzer.getWorkXYZ()

        self.do_command("$H")
        self.analyzer.Reset()
        self.analyzer.fastf = self.g0_feed
        machinePos, workPos = self.get_status(True)
        print machinePos, workPos
        self.analyzer.syncStatusWithGrbl(machinePos, workPos) # read the actual positions from grbl

        if any([coord != 0 for coord in oldMachineCoords]):
            res = QMessageBox.information(None, "Restore coords", "Move tool to previous position?", QMessageBox.Yes | QMessageBox.No)
            if res == QMessageBox.Yes:
                self.do_command("G53 G0 X%.3f Y%.3f" % (oldMachineCoords[0], oldMachineCoords[1]))
                self.do_command("G53 G0 Z%.3f" % (oldMachineCoords[2]))
                self.do_command("G10 P0 L20 X%.3f Y%.3f Z%.3f" % oldWorkCoords)

        self.position_updated.emit(self.analyzer.getPosition())



    def set_check_mode(self, checkMode):
        if self.checkMode != checkMode:
            self.do_command('$C')
            self.checkMode = checkMode
            time.sleep(0.5)
            self.serial.flushInput()

    def check_gcode_line(self, line):
        line = suppressAllInvalidGCodes(line)
        if not self.checkMode:
            self.set_check_mode(True)

        self.serial.flushInput()
        self.serial.write(line + '\n')
        while True:
            res = self.serial.readline()
            r = res.lower()
            if 'ok' in r:
                return True, None
            if 'error' in r or 'alarm' in r:
                return False, res

    def close(self):
        if self.serial is None:
            return
        self.serial.close()
        self.serial = None
        self.position_updated.emit([0, 0, 0])

    def reset(self):
        self.resetting = True
        try:
            self.serial.write("\x18")
        except:
            pass
        print "Resetting!"
        self.close()
        res = self.open()
        self.resetting = False
        return res

    def read_response(self, until="ok", ignoreInitialize = False):
        """
            read lines from the grbl until the expected matching line appears
            (usually "ok"), or just the first line if until is None.
        """
        result = []

        while True:
            while not self.serial.inWaiting > 0:
                QApplication.processEvents()
            line = self.serial.readline().strip()
            #print "Received line:", line
            if pycnc_config.SERIAL_DEBUG:
                if line == "": self.serial.write("\n")
            if line.startswith("error:") or line.startswith("ALARM:"):
                self.analyzer.undo()
                self.grbl_error.emit(line)
                break

            if not ignoreInitialize and line.startswith("Grbl"):
                # a spontaneous reset is detected?
                # restore work coordinates
                self.do_command("G10 P0 L20 X%.4f Y%.4f Z%.4f" % (self.analyzer.x, self.analyzer.y, self.analyzer.z))
                break

            result.append(line)
            if line == until or until == None:
                break
            time.sleep(0.1)

        return '\n'.join(result)

    def do_compensated_move(self, lastMoveCommand):
        if lastMoveCommand.isArc():  # arcs don't have a z movement: add one in the end
            lastMoveCommand.z += self.zCompensation.getZValue(lastMoveCommand.x, lastMoveCommand.y)
            self.serial.write(lastMoveCommand.getCommand() + '\n')
            self.read_response()  # wait for previous command to be acknowledged
            self.serial.write("G1 Z%.4f F100" % (lastMoveCommand.z))
            response = self.read_response()
        else:
            #print "Z compensation: original command ", lastMoveCommand.getCommand()
            for splitted_cmd in lastMoveCommand.splitMovement(self.zCompensation.spacing):
                #print "Z compensation: splitted command ", splitted_cmd.getCommand()
                #print "Z compensation: ",  self.zCompensation.getZValue(splitted_cmd.x, splitted_cmd.y)
                #print "Z compensation: ",  self.zCompensation.getZValue(splitted_cmd.x, splitted_cmd.y)
                splitted_cmd.z += self.zCompensation.getZValue(splitted_cmd.x, splitted_cmd.y)
                #print "Z compensation:      new command ", splitted_cmd.getCommand()
                self.serial.write(splitted_cmd.getCommand() + '\n')
                response = self.read_response()
        return response

    def do_command(self, gcode, wait=False, initCommand=False):
        """
            send the command to grbl, read the response and return it.
            if wait=True, wait for the stepper motion to complete before returning.
        """
        # self.waitAck = 0 # only for nonblocking commands, so it should be false, but if we run a nonblocking command, and then a blocking one, the blocking might catch the previous ok
        command = suppressAllInvalidGCodes(gcode.strip())
        if not command or command[0] == '(':
            return

        self.analyzer.Analyze(command)
        lastMoveCommand = self.analyzer.lastMovementGCode

        if (self.doZCompensation and
                self.zCompensation and
                not self.analyzer.relative and
                lastMoveCommand is not None): # z compensation only works in absolute coords
            response = self.do_compensated_move(lastMoveCommand)
        else: #business as usual
            self.serial.write(command)
            if pycnc_config.SERIAL_DEBUG:
                time.sleep(0.1)
            self.serial.write('\n')
            response = self.read_response(ignoreInitialize=initCommand)
        if wait:
            self.wait_motion()

        self.position_updated.emit(self.analyzer.getPosition())

        return response

    def do_command_nonblock(self, gcode):
        # run a command but don't wait
        command = suppressAllInvalidGCodes(gcode.strip())
        if not command or command[0] == '(':
            return
        self.waitAck += 1
        self.analyzer.Analyze(command)

        lastMoveCommand = self.analyzer.lastMovementGCode

        if (self.doZCompensation and
                self.zCompensation and
                not self.analyzer.relative and
                lastMoveCommand is not None): # z compensation only works in absolute coords
            self.do_compensated_move(lastMoveCommand)
            self.waitAck -= 1 # the do_compensated_move is blocking because it has to execute multiple commands. So remove the waitack.
        else: #business as usual
            self.serial.write(command + '\n')
        self.position_updated.emit(self.analyzer.getPosition())
        #print "Nonblock: wait ack status", self.waitAck

    def ack_received(self):
        if self.waitAck == 0: # waitAck is an integer because there can be more commands in the queue to be executed. TODO: test!
            return True, None # if waitAck is 0 it means that there are no commands in the pipeline. Can we send more than one command before ack? Maybe not...

        # there is no serial to be received, return false
        if not self.serial.inWaiting() > 0:
            return False, None

        line = self.serial.readline().strip()

        if line.startswith("Grbl"):
            # coordinates were reset
            self.restoreWorkCoords = True
            return False, line

        if line.startswith("error:") or line.startswith("ALARM:"):
            self.analyzer.undo()
            self.grbl_error.emit(line)
            self.waitAck -= 1
            if self.waitAck == 0:
                return True, line
            else:
                return False, line

        if line == "ok":
            self.waitAck -= 1
            if self.waitAck == 0:
                if self.restoreWorkCoords: # coordinates need to be restored
                    print "Restoring work coordinates"
                    self.do_command("G10 P0 L20 X%.4f Y%.4f Z%.4f" % (self.analyzer.x, self.analyzer.y, self.analyzer.z))
                    self.restoreWorkCoords = False

                return True, line
            else:
                return False, line

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
        self.serial.flushInput()
        self.do_command("G4 P0")


    def wait_motion_nonblock(self):
        self.do_command_nonblock("G4 P0")
        # self.motionWaiting = True
        # self.serial.flushInput()
        # self.serial.write("G4 P0\n")


    def load_config(self, grblLine=None):
        # query GRBL for the configuration
        conf = self.do_command("$$", initCommand=True)
        self.config = {}
        if grblLine is not None:
            # this is the Grbl welcome message
            m = re.search('Grbl ([0-9]+)\.([0-9]+)(.?)', grblLine)
            self.config['Major'] = int(m.group(1))
            self.config['Minor'] = int(m.group(2))
            self.config['Revision'] = m.group(3)
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

    def get_status(self, getBothStatuses = False):
        self.serial.write('?') # no newline needed
        res = self.read_response(None) # read one line
        # status is: <Idle,MPos:10.000,-5.000,2.000,WPos:0.000,0.000,0.000,Buf:0,RX:0,Ln:0,F:0.>
        #get machine and work pos
        # Grbl 1.1 only gives either machine or work pos!

        machineStatus = None
        workStatus = None

        m = re.search('MPos:([-.0-9]+),([-.0-9]+),([-.0-9]+)', res)
        if m is not None:
            machineStatus = {
                'status': res,
                'type': 'Machine',
                'position': ( float(m.group(1)), float(m.group(2)), float(m.group(3)) )
            }
            if not getBothStatuses:
                return machineStatus

        m = re.search('WPos:([-.0-9]+),([-.0-9]+),([-.0-9]+)', res)
        if m is not None:
            workStatus = {
                'status': res,
                'type': 'Work',
                'position': (float(m.group(1)), float(m.group(2)), float(m.group(3)))
            }
            if not getBothStatuses:
                return workStatus

        # if both statuses are none here, then we had an error
        if machineStatus is None and workStatus is None:
            if getBothStatuses:
                return None, None # we wanted both positions, so send two return values
            else:
                return None

        # only executed if getBothPositions is True!! This makes the following recursion safe
        # here it means that we want both positions. Find out which one we miss (if any). We are sure that we have at least one
        if machineStatus is None:
            # this means that we have Grbl1.1 and the status setting is "Work": switch to Machine
            self.do_command("$10=1")
            # get the other status
            machineStatus = self.get_status(False)
            self.do_command("$10=0")
            if machineStatus is None:
                return None, None # error
            else:
                return machineStatus, workStatus
        elif workStatus is None:
            # this means that we have Grbl1.1 and the status setting is "Work": switch to Machine
            self.do_command("$10=0")
            # get the other status
            workStatus = self.get_status(False)
            self.do_command("$10=1")
            if workStatus is None:
                return None, None  # error
            else:
                return machineStatus, workStatus
        else:
            return machineStatus, workStatus

    def do_probe(self):
        initial_status = self.get_status()
        probeResponse = self.do_command("G38.2 Z%.3f F%.3f" % (-math.fabs(pycnc_config.PROBING_DISTANCE),
                                                               pycnc_config.PROBING_FEED))  # probe z

        if 'ALARM' in probeResponse:
            self.probe_error.emit()
            return None, None, None

        end_status = self.get_status()

        x = end_status['position'][0] - initial_status['position'][0]
        y = end_status['position'][1] - initial_status['position'][1]
        z = end_status['position'][2] - initial_status['position'][2]

        print "Probe position:",x,y,z

        return x,y,z

    # this is not needed as it's not 100% Grbl1.1-compatible, as it relies on getting both the work and machine positions at the same time
    # def parse_probe_response(self, response):
    #     status = self.get_status()
    #     machineOffsetX = status['work'][0] - status['machine'][0]
    #     machineOffsetY = status['work'][1] - status['machine'][1]
    #     machineOffsetZ = status['work'][2] - status['machine'][2]
    #     lines = response.split('\n')
    #     for line in lines:
    #         print "Parsing probe response: ",line
    #         m = re.match("\[PRB:([-0-9.]+),([-0-9.]+),([-0-9.]+):[01]+\]", line)
    #         if m:
    #             return float(m.group(1))+machineOffsetX, float(m.group(2))+machineOffsetY, float(m.group(3))+machineOffsetZ
    #     return None, None, None

    def probe_z_offset(self):
        self.wait_motion()
        wasZComp = self.doZCompensation
        self.doZCompensation = False
        self.do_command("G90") # absolute positioning
        self.do_command("G10 P0 L20 Z0") # set current z to 0
        x,y,z = self.do_probe()
        self.do_command("G10 P0 L20 Z0") # set Z=0 on piece
        self.doZCompensation = wasZComp # restore Z compensation

        return z

    def probe_grid(self, xRange, yRange, spacing):
        self.zCompensation = ZCompensation(xRange, yRange, spacing)
        self.do_command("G90")
        probePoints = self.zCompensation.getProbePoints()
        self.do_command("G0 X" + str(probePoints[0][0]) + " Y" + str(probePoints[0][1])) # move to first probe point
        safeZ = -self.probe_z_offset()
        self.zCompensation.setZValue(0, 0.0) # set first point to z=0 by default
        for pointIndex in range(1, len(probePoints)):
            # move to next probe point
            self.do_command("G0 Z" + str(safeZ)) # move to safe height
            self.do_command("G0 X" + str(probePoints[pointIndex][0]) + " Y" + str(probePoints[pointIndex][1])) # move to probe point
            x, y, z = self.do_probe()
            if z is None:
                self.zCompensation = None
                return False
            self.zCompensation.setZValue(pointIndex, z)

        self.do_command("G0 Z" + str(safeZ))  # move to safe height
        return True

    def compensate_z(self, status = True):
        self.doZCompensation = status

    def update_position(self):
        pos = self.get_status()
        if pos == None: return
        self.analyzer.syncStatusWithGrbl(pos)
        self.position_updated.emit(self.analyzer.getPosition())

    def cancelJog(self):
        self.serial.write('\x85')
