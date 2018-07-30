#!/usr/bin/env python

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

from PySide.QtGui import *

from gcode.GrblWriterBasic import GrblWriterBasic
from gcode.GrblWriter import GrblWriter
from JogWidget.JogWidget import JogWidget
from RunWidget.RunWidget import RunWidget
from pyFileList.JoyFileList import JoyFileList
import sys
from splash_ui import Ui_Splash
import pygame
import time
import argparse
from string_format import config_string_format

def waitForJoy():
    pygame.init()
    pygame.joystick.init()
    #print "Number of joysticks:", pygame.joystick.get_count()
    while (pygame.joystick.get_count() == 0):
        pygame.quit()
        QApplication.processEvents()
        pygame.init()
        pygame.joystick.init()

class SplashWidget(QWidget, Ui_Splash):
    def __init__(self, parent = None):
        QWidget.__init__(self, parent)
        self.setupUi(self)

    def setText(self, txt):
        self.label.setText(txt)

class MainWindow(QStackedWidget):

    def __init__(self, parent=None):
        QStackedWidget.__init__(self,parent)
        self.resize(480, 320)

    def start_app(self, dummy = False):
        self.splash = SplashWidget(self)
        self.addWidget(self.splash)
        self.setCurrentWidget(self.splash)
        self.splash.AbortButton.clicked.connect(self.destroy)

        # do not require joystick
        #self.splash.setText("Waiting for joystick...")
        #QApplication.processEvents()

        #waitForJoy()

        self.splash.setText("Waiting for CNC...")
        QApplication.processEvents()

        if dummy:
            self.grblWriter = GrblWriterBasic()
        else:
            self.grblWriter = GrblWriter()
            self.grblWriter.grbl_error.connect(self.ask_perform_reset)

        # here wait for GRBL and show splash screen
        while not self.grblWriter.open():
            QApplication.processEvents()

        self.splash.setText("Initializing...")
        QApplication.processEvents()

        self.jogWidget = JogWidget()
        self.runWidget = RunWidget()
        self.fileListWidget = JoyFileList()

        self.runWidget.setGrbl(self.grblWriter)
        self.jogWidget.setGrbl(self.grblWriter)

        self.addWidget(self.jogWidget)
        self.addWidget(self.fileListWidget)
        self.addWidget(self.runWidget)

        self.jogWidget.load_event.connect(self.loadFile)
        self.jogWidget.run_event.connect(self.runFile)
        self.jogWidget.error_event.connect(self.grblError)
        self.jogWidget.exitButton.clicked.connect(self.exitRequest)

        self.fileListWidget.ok_clicked.connect(self.fileSelected)
        self.fileListWidget.cancel_clicked.connect(self.cancelFileSelected)

        # at the moment end and stop in the run widget have the same effect
        self.runWidget.end_event.connect(self.runEnd)
        self.runWidget.stop_event.connect(self.runEnd)
        self.runWidget.error_event.connect(self.grblError)
        self.runWidget.pause_event.connect(self.doPause) # when this is called, the pause was already generated

        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoggers()

    # changes the appearance of the jog widget to work during pause
    def _reconfigureJogWidget(self, pauseFlag):
        if pauseFlag:
            # repurpose jogwidget buttons
            try:
                self.jogWidget.run_event.disconnect(self.runFile)
            except:
                print "Can't jogWidget.run_event.disconnect(self.runFile)"
                pass

            try:
                self.jogWidget.load_event.disconnect(self.loadFile)
            except:
                print "Can't jogWidget.load_event.disconnect(self.loadFile)"
                pass
            self.jogWidget.RunButton.originalText = self.jogWidget.RunButton.text()
            self.jogWidget.RunButton.setText( config_string_format( QApplication.translate("joyWidget", "Cancel (%BTN_OK+1%)", None, QApplication.UnicodeUTF8)) )
            self.jogWidget.LoadButton.originalText = self.jogWidget.LoadButton.text()
            self.jogWidget.LoadButton.setText(config_string_format( QApplication.translate("joyWidget", "Resume (%BTN_CANCEL+1%)", None, QApplication.UnicodeUTF8)))

            self.jogWidget.run_event.connect(self.cancelPause)
            self.jogWidget.load_event.connect(self.doResume)
        else:
            try:
                self.jogWidget.run_event.disconnect(self.cancelPause)
            except:
                pass

            try:
                self.jogWidget.load_event.disconnect(self.doResume)
            except:
                pass

            self.jogWidget.RunButton.setText(self.jogWidget.RunButton.originalText)
            self.jogWidget.LoadButton.setText(self.jogWidget.LoadButton.originalText)
            self.jogWidget.run_event.connect(self.runFile)
            self.jogWidget.load_event.connect(self.loadFile)

    def ask_perform_reset(self, errorLine):
        if self.grblWriter.resetting:
            return

        if self.runWidget.running: # the run widget deals with errors on its own
            return
        res = QMessageBox.critical(self, "Grbl Error", "%s\nPerform reset?" % (errorLine),
                                      QMessageBox.Yes | QMessageBox.No)
        if res == QMessageBox.Yes:
            self.grblWriter.reset()

    # don't need to generate the pause, this is called when the system is already paused
    def doPause(self, pauseFlag):
        if not pauseFlag:
            return
        self._reconfigureJogWidget(True)
        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoggers()

    def doResume(self):
        self._reconfigureJogWidget(False)
        self.setCurrentWidget(self.runWidget)
        self.runWidget.resume()
        self.runWidget.startJoy()

    def cancelPause(self):
        self.runWidget.cancelPause()
        self._reconfigureJogWidget(False)
        self.jogWidget.startJoggers()

    def exitRequest(self):
        flags = QMessageBox.StandardButton.Yes
        flags |= QMessageBox.StandardButton.No
        question = QApplication.translate("cncController", "Do you really want to exit?", None, QApplication.UnicodeUTF8)
        response = QMessageBox.question(self, "Question",
                                              question,
                                              flags)
        if response == QMessageBox.Yes:
            self.jogWidget.stopJoggers()
            self.destroy()


    # function called when the jog widget wants to select a file: activate the fileListWidget
    def loadFile(self):
        # reload devices
        self.fileListWidget.populateDevices()
        # activate the widget
        self.setCurrentWidget(self.fileListWidget)
        self.fileListWidget.startJoy()

    # we get here from the listWidget: activate the jogwidget and load the file
    def fileSelected(self, filename):
        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoggers()
        QApplication.processEvents()
        self.jogWidget.loadFile(filename)

    # reactivate jogWidget without changing anything
    def cancelFileSelected(self, filename):
        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoggers()

    def runFile(self):
        if self.jogWidget.isFileLoaded == False:
            return

        self.setCurrentWidget(self.runWidget)
        self.runWidget.startJoy()
        self.runWidget.runGCode(self.jogWidget.file, self.jogWidget.gcode, self.jogWidget.times, self.jogWidget.totalTime, self.jogWidget.bBox)

    def runEnd(self):
        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoggers()

    def grblError(self):
        # reset grbl
        if self.grblWriter.resetting: # already resetting
            return
        self.setCurrentWidget(self.splash)
        self.splash.setText("GRBL Error. Reconnecting...")
        QApplication.processEvents()

        while not self.grblWriter.reset():
            time.sleep(0.5)

        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoggers()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A convenient GUI for CNC control")
    parser.add_argument("-f", "--fullscreen", action="store_true", help="make app fullscreen")
    parser.add_argument("-d", "--dummy", action="store_true", help="use dummy sender (debug)")

    args = parser.parse_args()

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create(u'Plastique'))
    window = MainWindow()
    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()

    window.start_app(args.dummy)
    sys.exit(app.exec_())




