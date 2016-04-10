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

def waitForJoy():
    pygame.init()
    pygame.joystick.init()
    #print "Number of joysticks:", pygame.joystick.get_count()
    while (pygame.joystick.get_count() == 0):
        pygame.quit()
        QApplication.processEvents()
        time.sleep(0.5)
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
        self.splash.setText("Waiting for joystick...")
        QApplication.processEvents()

        waitForJoy()

        self.splash.setText("Waiting for CNC...")
        QApplication.processEvents()

        if dummy:
            self.grblWriter = GrblWriterBasic()
        else:
            self.grblWriter = GrblWriter()

        # here wait for GRBL and show splash screen
        while not self.grblWriter.open():
            time.sleep(0.5)

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

        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoy()

    def exitRequest(self):
        flags = QMessageBox.StandardButton.Yes
        flags |= QMessageBox.StandardButton.No
        question = "Do you really want to exit?"
        response = QMessageBox.question(self, "Question",
                                              question,
                                              flags)
        if response == QMessageBox.Yes:
            self.jogWidget.stopJoy()
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
        self.jogWidget.startJoy()
        QApplication.processEvents()
        self.jogWidget.loadFile(filename)

    # reactivate jogWidget without changing anything
    def cancelFileSelected(self, filename):
        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoy()

    def runFile(self):
        if self.jogWidget.isFileLoaded == False:
            return

        self.setCurrentWidget(self.runWidget)
        self.runWidget.startJoy()
        self.runWidget.runGCode(self.jogWidget.file, self.jogWidget.gcode, self.jogWidget.times, self.jogWidget.totalTime, self.jogWidget.bBox)

    def runEnd(self):
        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoy()

    def grblError(self):
        # reset grbl
        self.setCurrentWidget(self.splash)
        self.splash.setText("GRBL Error. Reconnecting...")
        QApplication.processEvents()

        while not self.grblWriter.reset():
            time.sleep(0.5)

        self.setCurrentWidget(self.jogWidget)
        self.jogWidget.startJoy()



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




