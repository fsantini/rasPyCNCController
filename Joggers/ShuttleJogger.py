evdev_available = True
try:
    import evdev
except:
    evdev_available = False
import PySide.QtCore
import math
import time
import pycnc_config
from AbstractJogger import AbstractJogger

class WheelEventThread(PySide.QtCore.QThread):
    def __init__(self, jogger):
        PySide.QtCore.QThread.__init__(self)
        self.jogger = jogger
        self.active = False

    def start(self):
        self.killMe = False
        PySide.QtCore.QThread.start(self)

    def run(self):
        self.active = True
        while not self.killMe:
            if self.jogger.activeAxis != 0 and self.jogger.wheelStatus != 0:
                if self.jogger.activeAxis == 3: # Z axis
                    feed = pycnc_config.STD_FEED_Z
                else:
                    feed = pycnc_config.STD_FEED

                xyz = [0.0,0.0,0.0]
                xyz[self.jogger.activeAxis-1] = self.jogger.wheelStatus
                self.jogger.relative_move_event.emit(xyz, feed)
                time.sleep(float(pycnc_config.BTN_REPEAT) / 1000.0) # limit events to 1 each BTN_REPEAT

        self.active = False

    def stop(self):
        self.killMe = True

class ShuttleJogger(PySide.QtCore.QThread, AbstractJogger):

    # codes
    BUTTON_1 = pycnc_config.SHUTTLE_BUTTON_1
    BUTTON_2 = pycnc_config.SHUTTLE_BUTTON_2
    BUTTON_3 = pycnc_config.SHUTTLE_BUTTON_3
    BUTTON_4 = pycnc_config.SHUTTLE_BUTTON_4
    BUTTON_5 = pycnc_config.SHUTTLE_BUTTON_5

    BUTTONS = [BUTTON_1, BUTTON_2, BUTTON_3, BUTTON_4, BUTTON_5]
    XYZBUTTONS = [BUTTON_1, BUTTON_2, BUTTON_3]
    STEPSIZE = pycnc_config.SHUTTLE_STEPSIZES

    WHEEL = pycnc_config.SHUTTLE_WHEEL
    DIAL = pycnc_config.SHUTTLE_DIAL

    # values
    BUTTON_DOWN = 1
    BUTTON_UP = 0

    def __init__(self):
        PySide.QtCore.QThread.__init__(self)
        #AbstractJogger.__init__(self)
        self.shuttleDev = None
        self.killMe = False
        if not evdev_available:
            print "Evdev system not available!"
            return
        devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
        for dev in devices:
            if pycnc_config.SHUTTLE_IDENTIFIER in dev.name:
                self.shuttleDev = dev
                break

        if self.shuttleDev is None:
            print "Shuttle not found!"

        #self.relative_move_event.connect(self.printMove)
        self.wheelEventThread = WheelEventThread(self)
        self.jogWidget = None

    def printMove(self, xyz, feed):
        print xyz, "Feed", feed

    def start(self):
        if self.shuttleDev is None:
            print "Cannot start Shuttle jogger"
            return
        self.shuttleDev.grab()
        self.killMe = False

        # initialize events
        self.eventBlock = None
        self.dialStatus = None
        self.wheelStatus = 0
        self.activeAxis = 0
        self.currentStepSizeIndex = 0

        PySide.QtCore.QThread.start(self)
        time.sleep(0.1)

    def process_events(self):
        # process the event block
        if self.eventBlock is None:
            return

        if self.eventBlock.code in self.BUTTONS:
            #print "Button event"
            if self.eventBlock.value == self.BUTTON_DOWN:
                if self.eventBlock.code == self.BUTTON_1:
                    self.activeAxis = 1 # X
                elif self.eventBlock.code == self.BUTTON_2:
                    self.activeAxis = 2 # Y
                elif self.eventBlock.code == self.BUTTON_3:
                    self.activeAxis = 3 # z
                elif self.eventBlock.code == self.BUTTON_4:
                    # home the active axis
                    if self.activeAxis != 0:
                        homeList = [None, None, None]
                        homeList[self.activeAxis-1] = 0.0 # set the active axis coordinate to 0.0
                        self.home_update_event.emit(homeList)
                elif self.eventBlock.code == self.BUTTON_5:
                    #change step size for dial jog
                    self.currentStepSizeIndex += 1
                    if self.currentStepSizeIndex >= len(self.STEPSIZE):
                        self.currentStepSizeIndex = 0

                    self.jogWidget.posGroup.setTitle("%s - Step: %.1f" % (self.originalText, self.STEPSIZE[self.currentStepSizeIndex]))

            if self.eventBlock.value == self.BUTTON_UP: # if an axis button is released, disable motion control
                if self.eventBlock.code in self.XYZBUTTONS:
                    self.activeAxis = 0


        if self.eventBlock.code == self.WHEEL:
            self.wheelStatus = pycnc_config.SHUTTLE_WHEEL_TO_MOVEMENT_TRANSFORMATION(self.eventBlock.value)

        if self.eventBlock.code == self.DIAL:
            self.wheelStatus = 0 # a dial event sets the wheel to 0
            if self.dialStatus is None:
                self.dialStatus = self.eventBlock.value

            currentDelta = self.eventBlock.value - self.dialStatus
            if math.fabs(currentDelta) > 100: # the rotary encoder overflowed
                if currentDelta < 0:
                    currentDelta = 255 + currentDelta
                else:
                    currentDelta = currentDelta - 255

            self.dialStatus = self.eventBlock.value

            if self.activeAxis != 0:
                xyz = [0.0,0.0,0.0]
                xyz[self.activeAxis-1] = float(currentDelta) * self.STEPSIZE[self.currentStepSizeIndex]
                self.relative_move_event.emit(xyz, -1)

        if self.activeAxis != 0 and self.wheelStatus != 0:
            if not self.wheelEventThread.active:
                self.wheelEventThread.start()
        else:
            if self.wheelEventThread.active:
                self.wheelEventThread.stop()

        self.eventBlock = None

    def run(self):
        if self.shuttleDev is None:
            print "Cannot start Shuttle jogger"
            return

        for event in self.shuttleDev.read_loop():
            if self.killMe:
                return

            if event.code == evdev.ecodes.SYN_REPORT:
                self.process_events() # the block is closed
                continue
            if event.code == self.WHEEL:
                self.eventBlock = event # this is the most important event
                continue

            if event.code in self.BUTTONS:
                self.eventBlock = event
                continue

            # a dial event is always sent; only process it if there is no other event in the pipeline
            if event.code == self.DIAL and self.eventBlock is None:
                self.eventBlock = event
                continue


    def stop(self):
        self.killMe = True
        self.wheelEventThread.stop()
        time.sleep(0.1)
        self.shuttleDev.ungrab()

    # attach this jogger to a particular widget. Use for example to install a keyboard filter
    def install(self, widget):
        self.jogWidget = widget
        self.originalText = widget.posGroup.title()

if __name__ == '__main__':


    jogger = ShuttleJogger()
    print jogger.shuttleDev.capabilities(verbose=True)
    jogger.start()
    time.sleep(30)
    print "Stopping..."
    jogger.stop()


