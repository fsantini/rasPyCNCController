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
# This code is modified from RepetierHost - Original copyright and license:
# Copyright 2011 repetier repetierdev@gmail.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import math
import fileinput
import sys
import os
from gcodeconv import GCodeConverter

def euclidean_distance(start, end):
    return math.sqrt(sum([(e - s) ** 2 for (s, e) in zip(start, end)]))


def arc_distance(center, start, end, ccw):
    startRel = (start[0] - center[0], start[1] - center[1])
    endRel = (end[0] - center[0], end[1] - center[1])
    radius = euclidean_distance(center, start)
    startAngle = (math.atan2(startRel[1], startRel[0]) + 2 * math.pi) % (2 * math.pi)
    endAngle = (math.atan2(endRel[1], endRel[0]) + 2 * math.pi) % (2 * math.pi)
    travelAngle = endAngle - startAngle
    if not ccw: travelAngle = -travelAngle  # if the circle is clockwise, then invert the angle
    travelAngle = travelAngle % (2 * math.pi)  # if angle is negative, it actually means that it's 360 - angle
    return travelAngle * radius

class MovementGCode:
    def __init__(self, g):
        self.g = g
        self.x = None
        self.y = None
        self.i = None
        self.j = None
        self.z = None
        self.e = None
        self.f = None
        self.startX = None
        self.startY = None
        self.startZ = None

    def getCommand(self):
        cmd = "G" + str(self.g)
        if self.x is not None: cmd += " X%.4f" % (self.x)
        if self.y is not None: cmd += " Y%.4f" % (self.y)
        if self.g == 0 or self.g == 1:
            if self.z is not None: cmd += " Z%.4f" % (self.z)
        elif self.g == 2 or self.g == 3:
            if self.i is not None: cmd += " I%.4f" % (self.i)
            if self.j is not None: cmd += " J%.4f" % (self.j)

        if self.e is not None: cmd += " E%.4f" % (self.e)
        if self.f is not None: cmd += " F%.4f" % (self.f)
        return cmd

    def splitMovement(self, maxDistance):
#        print "Splitting movement",(self.startX, self.startY, self.startZ), (self.x, self.y, self.z)
#        print "Original G", self.getCommand()
        if (self.startX is None or
            self.startY is None or
            self.startZ is None or
            self.e is not None or
            self.isArc()): # arc will not be split
            return [self]

        myDistance = euclidean_distance( (self.startX, self.startY, self.startZ), (self.x, self.y, self.z) )
        #print "My distance:", myDistance
        if myDistance <= maxDistance:
            return [self]

        midpointX = (self.startX + self.x) / 2
        midpointY = (self.startY + self.y) / 2
        midpointZ = (self.startZ + self.z) / 2

#        print "mid point: ", midpointX, midpointY, midpointZ

        # now split the movement in the middle
        firstMovement = MovementGCode(self.g)

        firstMovement.f = self.f

        firstMovement.startX = self.startX
        firstMovement.startY = self.startY
        firstMovement.startZ = self.startZ

        firstMovement.x = midpointX
        firstMovement.y = midpointY
        firstMovement.z = midpointZ

#        print "first movement", firstMovement

        secondMovement = MovementGCode(self.g)

        secondMovement.f = self.f

        secondMovement.startX = midpointX
        secondMovement.startY = midpointY
        secondMovement.startZ = midpointZ

        secondMovement.x = self.x
        secondMovement.y = self.y
        secondMovement.z = self.z

#        print "second movement", secondMovement

        outList = [] # recursively split movements
        outList.extend(firstMovement.splitMovement(maxDistance))
        outList.extend(secondMovement.splitMovement(maxDistance))

        return outList

    def __repr__(self):
        return self.getCommand()

    def isArc(self):
        return self.g == 2 or self.g == 3


def safeInt(val):
    try:
        return int(val)
    except:
        return 0


def safeFloat(val):
    try:
        return float(val)
    except:
        return 0


# find a code in a gstring line
def findCode(gcode, codeStr):
    pattern = re.compile(codeStr + "\\s*(-?[\d.]*)", re.I)
    m = re.search(pattern, gcode)
    if m == None:
        return None
    else:
        return m.group(1)




class GCodeAnalyzer():
    def __init__(self, calculateTravel=True):
        self.Reset()
        self.converter = GCodeConverter()
        self.calculateTravel = calculateTravel

    def Reset(self):
        self.x = 0
        self.y = 0
        self.z = 0
        self.e = 0
        self.emax = 0
        self.f = 1000  # standard feed rate
        self.fastf = 5000  # fast feed rate for g0 moves
        self.lastX = 0
        self.lastY = 0
        self.lastZ = 0
        self.lastE = 0
        self.xOffset = 0
        self.yOffset = 0
        self.zOffset = 0
        self.eOffset = 0
        self.lastZPrint = 0
        self.layerZ = 0
        self.relative = False
        self.eRelative = False
        self.homeX = 0
        self.homeY = 0
        self.homeZ = 0
        self.lastMovementGCode = None
        self.lastGCodeLine = ""
        self.metric = True

        # for G162: home to maximum
        self.axisMaxX = 150
        self.axisMaxY = 150
        self.axisMaxZ = 150

        # bounding box
        self.maxX = 0
        self.maxY = 0
        self.maxZ = 0
        self.minX = 0
        self.minY = 0
        self.minZ = 0

        self.hasHomeX = False
        self.hasHomeY = False
        self.hasHomeZ = False
        self.travel = 0
        self.time = 0  # time in minutes

        self.moveInMachineCoords = False

    # undo one movement gcode command (does not affect bouding box)
    def undo(self):
        #if self.lastMovementGCode is None: return
        self.x = self.lastX
        self.y = self.lastY
        self.z = self.lastZ
        self.e = self.lastE
        self.lastMovementGCode = None

    def Analyze(self, gcode):
        self.lastGCodeLine = gcode
        if gcode.find(";") >= 0:
            gcode = gcode[:gcode.find(";")]  # remove comments
        if gcode.find("(") >= 0:
            gcode = gcode[:gcode.find("(")]  # remove comments
        if gcode.find("$") >= 0:
            gcode = gcode[:gcode.find("$")]  # ignore configuration/jog commands

        tokens = ['']
        # convert multiple G commands on one line
        tokens.extend(re.split('([GM][^GM]+)', gcode, re.I))
        for line in tokens:
            if line.strip() != "":
                # print "Analyze ", line
                self.AnalyzeLine(self.converter.convert(line))  # handles grbl-style code

        self.moveInMachineCoords = False # this flag gets reset at the end of the gcode line

    def AnalyzeLine(self, gcode):
        self.lastMovementGCode = None  # by default, the move was not a g[0-3]; set it differently in case of actual movement gcode

        gcode = gcode.lstrip();
        if gcode.startswith("@"): return  # code is a host command

        code_g = findCode(gcode, "G")
        if '$H' in gcode:
            code_g = str(28) # this is a homing command equivalent to g28
        code_m = findCode(gcode, "M")
        # we have a g_code
        if code_g != None:
            if '.' in code_g: # codes like 38.2 were considered G0!
                code_g = safeFloat(code_g)
            else:
                code_g = safeInt(code_g)

            if (self.metric):
                metricConv = 1
            else:
                metricConv = 25.4

            # get movement codes
            if code_g == 0 or code_g == 1 or code_g == 2 or code_g == 3:
                self.lastX = self.x
                self.lastY = self.y
                self.lastZ = self.z
                self.lastE = self.e
                eChanged = False;
                code_f = findCode(gcode, "F")
                if code_f != None:
                    self.f = safeFloat(code_f) * metricConv

                code_x = findCode(gcode, "X")
                code_y = findCode(gcode, "Y")
                code_z = findCode(gcode, "Z")
                code_e = findCode(gcode, "E")

                if self.moveInMachineCoords: # convert the machine coords move to work coords
                    print "Move is in machine coords!"
                    if code_x is not None:
                        code_x = safeFloat(code_x) + self.xOffset

                    if code_y is not None:
                        code_y = safeFloat(code_y) + self.yOffset

                    if code_y is not None:
                        code_z = safeFloat(code_z) + self.zOffset


                code_i = findCode(gcode, "I")
                code_j = findCode(gcode, "J")

                self.lastMovementGCode = MovementGCode(code_g)
                self.lastMovementGCode.startX = self.lastX/metricConv
                self.lastMovementGCode.startY = self.lastY/metricConv
                self.lastMovementGCode.startZ = self.lastZ/metricConv
                self.lastMovementGCode.x = safeFloat(code_x or self.lastX/metricConv)
                self.lastMovementGCode.y = safeFloat(code_y or self.lastY/metricConv)
                self.lastMovementGCode.z = safeFloat(code_z or self.lastZ/metricConv)
                if code_g == 2 or code_g == 3:
                    self.lastMovementGCode.i = safeFloat(code_i)
                    self.lastMovementGCode.j = safeFloat(code_j)

                if code_e:
                    self.lastMovementGCode.e = safeFloat(code_e)

                if code_f:
                    self.lastMovementGCode.f = safeFloat(code_f)


                if self.relative:
                    if code_x != None: self.x += safeFloat(code_x) * metricConv
                    if code_y != None: self.y += safeFloat(code_y) * metricConv
                    if code_z != None: self.z += safeFloat(code_z) * metricConv
                    if code_e != None:
                        e = safeFloat(code_e) * metricConv
                        if e != 0:
                            eChanged = True
                            self.e += e
                else:
                    # absolute coordinates
                    if code_x != None: self.x =  safeFloat(code_x) * metricConv
                    if code_y != None: self.y =  safeFloat(code_y) * metricConv
                    if code_z != None: self.z =  safeFloat(code_z) * metricConv
                    if code_e != None:
                        e = safeFloat(code_e) * metricConv
                        if self.eRelative:
                            if e != 0:
                                eChanged = True
                                self.e += e
                        else:
                            # e is absolute. Is it changed?
                            if self.e != self.eOffset + e:
                                eChanged = True
                                self.e = self.eOffset + e
                # bbox calculation
                if self.x < self.minX: self.minX = self.x
                if self.y < self.minY: self.minY = self.y
                if self.z < self.minZ: self.minZ = self.z

                if self.x > self.maxX: self.maxX = self.x
                if self.y > self.maxY: self.maxY = self.y
                if self.z > self.maxZ: self.maxZ = self.z

                travel_len = 0
                travel_time = 0
                # calculate travelled distance. Quite time consuming, so only do it if needed.
                if self.calculateTravel:
                    if code_g == 0 or code_g == 1:
                        travel_len = euclidean_distance((self.lastX, self.lastY, self.lastZ), (self.x, self.y, self.z))
                        if code_g == 0:
                            travel_time = travel_len / self.fastf
                        else:
                            travel_time = travel_len / self.f
                    else:
                        # it's an arc: get the center
                        centerX = self.lastX + safeFloat(code_i) * metricConv
                        centerY = self.lastY + safeFloat(code_j) * metricConv
                        ccw = True if code_g == 3 else False  # g3 is counter clockwise arc
                        travel_len = arc_distance((centerX, centerY), (self.lastX, self.lastY), (self.x, self.y), ccw)
                        travel_time = travel_len / self.f

                self.travel += travel_len
                self.time += travel_time

                # Repetier has a bunch of limit-checking code here and time calculations: we are leaving them for now
            elif code_g == 20:
                self.metric = False
            elif code_g == 21:
                self.metric = True
            elif code_g == 28 or code_g == 161:
                self.lastX = self.x
                self.lastY = self.y
                self.lastZ = self.z
                self.lastE = self.e
                code_x = findCode(gcode, "X")
                code_y = findCode(gcode, "Y")
                code_z = findCode(gcode, "Z")
                code_e = findCode(gcode, "E")
                homeAll = False
                if code_x == None and code_y == None and code_z == None: homeAll = True
                if code_x != None or homeAll:
                    self.hasHomeX = True
                    self.xOffset = 0
                    self.x = self.homeX
                if code_y != None or homeAll:
                    self.hasHomeY = True
                    self.yOffset = 0
                    self.y = self.homeY
                if code_z != None or homeAll:
                    self.hasHomeZ = True
                    self.zOffset = 0
                    self.z = self.homeZ
                if code_e != None:
                    self.eOffset = 0
                    self.e = 0
            # elif code_g == 162:
            #     self.lastX = self.x
            #     self.lastY = self.y
            #     self.lastZ = self.z
            #     self.lastE = self.e
            #     code_x = findCode(gcode, "X")
            #     code_y = findCode(gcode, "Y")
            #     code_z = findCode(gcode, "Z")
            #     homeAll = False
            #     if code_x == None and code_y == None and code_z == None: homeAll = True
            #     if code_x != None or homeAll:
            #         self.hasHomeX = True
            #         self.xOffset = 0
            #         self.x = self.axisMaxX
            #     if code_y != None or homeAll:
            #         self.hasHomeY = True
            #         self.yOffset = 0
            #         self.y = self.axisMaxY
            #     if code_z != None or homeAll:
            #         self.hasHomeZ = True
            #         self.zOffset = 0
            #         self.z = self.axisMaxZ
            elif code_g == 53:
                self.moveInMachineCoords = True
            elif code_g == 90:
                self.relative = False
            elif code_g == 91:
                self.relative = True
            elif code_g == 92 or code_g == 10:
                code_x = findCode(gcode, "X")
                code_y = findCode(gcode, "Y")
                code_z = findCode(gcode, "Z")
                code_e = findCode(gcode, "E")

                current_machine_coords = self.getMachineXYZ()

                if code_x != None:
                    self.x = safeFloat(code_x) * metricConv

                if code_y != None:
                    self.y = safeFloat(code_y) * metricConv

                if code_z != None:
                    self.z = safeFloat(code_z) * metricConv

                if code_e != None:
                    self.e = safeFloat(code_e) * metricConv

                #redefine offsets x = machine_x + offset => offset = x - machine_x
                self.xOffset = self.x - current_machine_coords[0]
                self.yOffset = self.y - current_machine_coords[1]
                self.zOffset = self.z - current_machine_coords[2]



                # the following code is correct for 3D printers and Marlin. With Grbl, the position is factually redefined
                # if code_x != None:
                #   self.xOffset = self.x - safeFloat(code_x)
                #   self.x = self.xOffset
                # if code_y != None:
                #   self.yOffset = self.y - safeFloat(code_y)
                #   self.y = self.yOffset
                # if code_z != None:
                #   self.zOffset = self.z - safeFloat(code_z)
                #   self.z = self.zOffset
                # if code_e != None:
                #   self.eOffset = self.e - safeFloat(code_e)
                #   self.e = self.eOffset
        if code_m != None:
            code_m = safeInt(code_m)
            if code_m == 82:
                self.eRelative = False
            elif code_m == 83:
                self.eRelative = True

    #    self.print_status()

    def getMachineXYZ(self):
        return self.x - self.xOffset, self.y - self.yOffset, self.z - self.zOffset

    def getWorkXYZ(self):
        return self.x, self.y, self.z

    def syncStatusWithGrbl(self, grblMachineStatus, grblWorkStatus = None):
        if grblWorkStatus is None:
            # we only have one status report. Update the correct coordinates
            if grblMachineStatus['type'] == 'Work':
                self.x, self.y, self.z = grblWorkStatus['position']
            else:
                self.x = grblMachineStatus['position'][0] + self.xOffset
                self.y = grblMachineStatus['position'][1] + self.yOffset
                self.z = grblMachineStatus['position'][2] + self.zOffset
        else:
            self.x, self.y, self.z = grblWorkStatus['position']

            self.xOffset = grblWorkStatus['position'][0] - grblMachineStatus['position'][0]
            self.yOffset = grblWorkStatus['position'][1] - grblMachineStatus['position'][1]
            self.zOffset = grblWorkStatus['position'][2] - grblMachineStatus['position'][2]


    def getBoundingBox(self):
        return (self.minX, self.minY, self.minZ), (self.maxX, self.maxY, self.maxZ)

    def getPosition(self):
        return (self.x, self.y, self.z)

    def getTravelLen(self):
        return self.travel

    def getTravelTime(self):
        return self.time

    def print_status(self):
        attrs = vars(self)
        print '\n'.join("%s: %s" % item for item in attrs.items())

    # returns true if the last move intersected the x value
    def intersected(self, xValue):
        if self.lastMovementGCode is None: return False
        if (self.lastX <= xValue and self.x >= xValue) or (self.lastX >= xValue and self.x <= xValue): return True
        return False

    # returns -1 if the last movement was towards -x, +1 if it was towards +x, 0 otherwise
    def movementDirection(self):
        if self.lastMovementGCode is None: return 0
        if self.lastX < self.x: return 1
        if self.lastX > self.x: return -1
        return 0


if __name__ == "__main__":
    analyzer = GCodeAnalyzer()
    for line in fileinput.input():
        analyzer.Analyze(line)
        # print line, analyzer.getPosition()

    print "Bounding box:", analyzer.getBoundingBox()
    print "Travel distance:", analyzer.getTravelLen()
    print "Travel time:", analyzer.getTravelTime()
