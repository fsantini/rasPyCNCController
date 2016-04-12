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
import JoyStatus
import pygame.event
import time
import pycnc_config
import sys

class JoyJogThread(PySide.QtCore.QThread):

    position_updated = PySide.QtCore.Signal(object)
    exit_event = PySide.QtCore.Signal(object)
    error_event = PySide.QtCore.Signal(object)

    # grblWriter is a class that supports do_command
    def __init_(self):
        PySide.QtCore.QThread.__init__(self)
        self.killMe = False
        self.grblWriter = None

    def setGrbl(self, grblWriter):
        self.grblWriter = grblWriter

    def start(self):
        self.killMe = False
        time.sleep(0.1)
        PySide.QtCore.QThread.start(self)

    def run(self):
        if self.grblWriter == None:
            return

        try:
            self.grblWriter.do_command("G21") # set mm
            self.grblWriter.do_command("G91") # incremental step mode
        except:
            e = sys.exc_info()[0]
            self.error_event.emit("%s" % e)
            return

        self.joy = JoyStatus.JoyStatus()

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

                cmd = "G01 X%.3f Y%.3f Z%.3f F%d" % (xyz[0], xyz[1], xyz[2], feed)
                myXYZ[0] += xyz[0]
                myXYZ[1] += xyz[1]
                myXYZ[2] += xyz[2]
                self.position_updated.emit(myXYZ)
                # print cmd
                try:
                    self.grblWriter.do_command(cmd, True)
                except:
                    e = sys.exc_info()[0]
                    self.error_event.emit("%s" % e)
                    return

            if self.joy.getButton(pycnc_config.BTN_ZERO):
                #print "\rSetting zero                          "
                myXYZ = [0, 0, 0]
                self.position_updated.emit(myXYZ)
                try:
                    self.grblWriter.do_command("G92 X0 Y0 Z0")  # set home with button 0
                except:
                    e = sys.exc_info()[0]
                    self.error_event.emit("%s" % e)
                    return

            if self.joy.getButton(pycnc_config.BTN_ZEROZ):
                #print "\rSetting zero                          "
                myXYZ[2] = 0
                self.position_updated.emit(myXYZ)
                try:
                    self.grblWriter.do_command("G92 Z0")  # set home with button 0
                except:
                    e = sys.exc_info()[0]
                    self.error_event.emit("%s" % e)
                    return

            if self.joy.getButton(pycnc_config.BTN_HOME):
                #print "\rGoing home                            "
                myXYZ = [0, 0, 0]
                #sys.stdout.write("\rX: %.3f, Y: %.3f, Z: %.3f           " % (myXYZ[0], myXYZ[1], myXYZ[2]))
                #sys.stdout.flush()
                try:
                    self.grblWriter.do_command("G90")
                    self.grblWriter.do_command("G00 X0 Y0 Z0", True)  # go to home
                    self.grblWriter.do_command("G91")
                except:
                    e = sys.exc_info()[0]
                    self.error_event.emit("%s" % e)
                    return
                self.position_updated.emit(myXYZ)

            if self.joy.getButton(pycnc_config.BTN_OK):
                # exit with true
                self.exit_event.emit(True)
                break

            if self.joy.getButton(pycnc_config.BTN_CANCEL):
                self.exit_event.emit(False)
                break

        #pygame.quit()

        try:
            self.grblWriter.do_command("G90") # absolute positioning
        except:
            e = sys.exc_info()[0]
            self.error_event.emit("%s" % e)

    def stop(self):
        self.killMe = True

class GrblWriter_debug:
    def do_command(self, cmd, wait = False):
        print(cmd)
        time.sleep(0.1)

if __name__=='__main__':
    writer_dbg = GrblWriter_debug()
    jogThread = JoyJogThread()
    jogThread.setGrbl(writer_dbg)
    jogThread.start()
    print "press return to exit"
    raw_input()
