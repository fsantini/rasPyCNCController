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
import pyJoy.JoyStatus
import pygame.event
import time
import pycnc_config
from AbstractJogger import AbstractJogger


class JoyJogThread(PySide.QtCore.QThread, AbstractJogger):

    def __init_(self):
        PySide.QtCore.QThread.__init__(self)
        AbstractJogger.__init__(self)
        self.killMe = False

    def start(self):
        self.killMe = False
        time.sleep(0.1)
        PySide.QtCore.QThread.start(self)
        time.sleep(0.1)

    def run(self):
        self.joy = pyJoy.JoyStatus.JoyStatus()

        myXYZ = [0,0,0]


        while (not self.killMe):
            time.sleep(0.1)
            pygame.event.get()
            xyz = self.joy.getXYZ()
            if xyz != (0, 0, 0):
                # go slower in Z moves
                if xyz[2] != 0:
                    feed = pycnc_config.STD_FEED_Z
                else:
                    feed = pycnc_config.STD_FEED

                # run command and wait for it to finish

                #cmd = "G01 X%.3f Y%.3f Z%.3f F%d" % (xyz[0], xyz[1], xyz[2], feed)
                myXYZ[0] += xyz[0]
                myXYZ[1] += xyz[1]
                myXYZ[2] += xyz[2]
                self.relative_move_event.emit(xyz, feed)
                # print cmd

            if self.joy.getButton(pycnc_config.BTN_ZERO):
                #print "\rSetting zero                          "
                myXYZ = [0, 0, 0]
                self.home_update_event.emit(myXYZ)

            if self.joy.getButton(pycnc_config.BTN_ZEROZ):
                #print "\rSetting zero                          "
                myXYZ[2] = 0
                self.home_update_event.emit([None, None, 0])

            if self.joy.getButton(pycnc_config.BTN_HOME):
                #print "\rGoing home                            "
                myXYZ = [0, 0, 0]
                self.absolute_move_event.emit(myXYZ, None)

            if self.joy.getButton(pycnc_config.BTN_OK):
                # exit with true
                self.exit_event.emit(True)
                break

            if self.joy.getButton(pycnc_config.BTN_CANCEL):
                self.exit_event.emit(False)
                break

    def stop(self):
        self.killMe = True
        time.sleep(0.1)

    # attach this jogger to a particular widget. Use for example to install a keyboard filter
    def install(self, widget):
        pass

if __name__=='__main__':
    jogThread = JoyJogThread()
    jogThread.start()
    print "press return to exit"
    raw_input()
