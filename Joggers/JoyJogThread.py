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

import PySide.QtCore
from pyJoy.JoyEvdev import JoyEvdev
import time
import pycnc_config
from AbstractJogger import AbstractJogger
import math

EVENT_INTERVAL = pycnc_config.BTN_REPEAT

class JoyJogThread(JoyEvdev, AbstractJogger): # order is important. Like this, JoyEvdev overrides the start and stop methods from AbstractJogger

    def __init__(self):
        JoyEvdev.__init__(self)
        self.accumulatedMove = None
        self.eventTimer = PySide.QtCore.QTimer(self)
        self.eventTimer.timeout.connect(self.sendMoveEvent)
        self.movementConfig = [pycnc_config.JOY_XAXIS_MAP, pycnc_config.JOY_YAXIS_MAP, pycnc_config.JOY_ZAXIS_MAP]
        self.parent = None



    def processButtonMovement(self, buttonNumber, value):
        val = 1 if value == self.BUTTON_DOWN else 0
        for movementAxis, config in enumerate(self.movementConfig):
            if buttonNumber in config['btns']:
                if self.accumulatedMove is None:
                    self.accumulatedMove = [0,0,0]
                self.accumulatedMove[movementAxis] = val * config['btnsMult'][config['btns'].index(buttonNumber)]

    def processAxisMovement(self, axisCode, value):
        for movementAxis, config in enumerate(self.movementConfig):
            if axisCode in config['axes']:
                if self.accumulatedMove is None:
                    self.accumulatedMove = [0,0,0]
                self.accumulatedMove[movementAxis] = config['axesMult'][config['axes'].index(axisCode)] * value

    def processHatMovement(self, hatCode, value):
        for movementAxis, config in enumerate(self.movementConfig):
            if hatCode in config['hats']:
                if self.accumulatedMove is None:
                    self.accumulatedMove = [0,0,0]
                self.accumulatedMove[movementAxis] = config['hatsMult'][config['hats'].index(hatCode)] * value

    def processButton(self, code, value):
        buttonNumber = pycnc_config.JOY_BUTTONS.index(code)

        if value == self.BUTTON_DOWN:
            if buttonNumber == pycnc_config.BTN_ZERO:
                self.home_update_event.emit([0, 0, 0])
            elif buttonNumber == pycnc_config.BTN_ZEROZ:
                self.home_update_event.emit([None, None, 0])
            elif buttonNumber == pycnc_config.BTN_HOME:
                self.absolute_move_event.emit([0, 0, 0], -1)  # None doen't work here for some reason
            elif buttonNumber == pycnc_config.BTN_OK:
                # exit with true
                self.exit_event.emit(True)
                #self.stop() # ??
            elif buttonNumber == pycnc_config.BTN_CANCEL:
                self.exit_event.emit(False)
                #self.stop() # ??

        self.processButtonMovement(buttonNumber, value)

    def processAxes(self, axesCode, value):
        self.processAxisMovement(axesCode, value)

    def processHat(self, hatCode, value):
        self.processHatMovement(hatCode, value)

    def sendMoveEvent(self):
        xyz = self.accumulatedMove

        # go slower in Z moves
        if xyz[2] != 0:  # Z axis
            minFeed = pycnc_config.MIN_FEED_Z
            maxFeed = pycnc_config.MAX_FEED_Z
        else:
            minFeed = pycnc_config.MIN_FEED
            maxFeed = pycnc_config.MAX_FEED

        feed = minFeed + int(math.sqrt(xyz[0] ** 2 + xyz[1] ** 2 + xyz[2] ** 2) * (maxFeed - minFeed) / 10)
        # feed = int(math.sqrt(xyz[0]**2 + xyz[1]**2 + xyz[2]**2)*maxFeed)
        if feed < minFeed: feed = minFeed
        if feed > maxFeed: feed = maxFeed

        self.relative_move_event.emit(xyz, feed)
        # print cmd

    def processSYN(self):
        #print "Syn received", self.accumulatedMove
        if self.accumulatedMove is None:
            return

        # send the move event
        if all([move == 0 for move in self.accumulatedMove]):
            self.relative_move_event.emit(self.accumulatedMove, 1000) # this is to stop a jog if Grbl1.1 is used
            self.accumulatedMove = None
            if self.eventTimer.isActive():
                print "Stopping timer"
                self.eventTimer.stop()
            return

        # keep sending events to keep jogging while a button is pressed
        if not self.eventTimer.isActive():
            self.eventTimer.start(EVENT_INTERVAL)

        self.sendMoveEvent()  # send one event now

    # attach this jogger to a particular widget. Use for example to install a keyboard filter
    def install(self, widget):
        self.parent = widget
        pass

if __name__=='__main__':
    jogThread = JoyJogThread()
    jogThread.start()
    print "press return to exit"
    raw_input()
