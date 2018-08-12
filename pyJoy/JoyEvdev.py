evdev_available = True
try:
    import evdev
except:
    evdev_available = False
import PySide.QtCore
import math
import time
import pycnc_config
#import traceback

def findAxisTuple(code, codeDoubleList):
    for axisN, axis in enumerate(codeDoubleList):
        try:
            return (axisN, axis.index(code)) # if axis contains the code, then return 0 if the code is in position 0, 1 if in pos 1. E.g. The JOY_HATS are [ [100,101], [102,103] ]. Code is 102. This function will return (1,0)
        except:
            pass
    return None

def findHatAxisTuple(code):
    return findAxisTuple(code, pycnc_config.JOY_HATS)

def findAxesAxisTuple(code):
    return findAxisTuple(code, pycnc_config.JOY_AXES)

def isButton(code):
    return code in pycnc_config.JOY_BUTTONS

class JoyEvdev(PySide.QtCore.QThread):

    # values
    BUTTON_DOWN = 1
    BUTTON_UP = 0

    def __init__(self):
        PySide.QtCore.QThread.__init__(self)
        self.joyDev = None
        self.killMe = False
        if not evdev_available:
            print "Evdev system not available!"
            return
        devices = [evdev.InputDevice(fn) for fn in evdev.list_devices()]
        for dev in devices:
            if pycnc_config.JOY_IDENTIFIER in dev.name:
                self.joyDev = dev
                break

        if self.joyDev is None:
            print "Joystick not found!"

    # redefine these stubs to do something useful in subclasses
    def processButton(self, code, value):
        pass

    def processHat(self, hatCode, value):
        pass

    def processAxes(self, axesCode, value):
        pass

    # this is called at the end of the event block, in case we want to process multiple events together (e.g. diagonal moves)
    def processSYN(self):
        pass

    def start(self):
        if self.joyDev is None:
            print "Cannot start Joystick"
            return

        # traceback.print_stack()
        self.joyDev.grab()
        self.killMe = False

        # initialize events
        self.eventBlock = None
        PySide.QtCore.QThread.start(self)
        time.sleep(0.1)

    def process_events(self):
        # process the event block
        if self.eventBlock is None:
            return

        #print "Event type", self.eventBlock.type, "Event code", self.eventBlock.code, "Value:", self.eventBlock.value

        if self.eventBlock.type == 0 and self.eventBlock.code == evdev.ecodes.SYN_REPORT:
            self.processSYN()
            self.eventBlock = None
            return

        if isButton(self.eventBlock.code):
            # print "Button event"
            self.processButton(self.eventBlock.code, self.eventBlock.value)

        hatCode = findHatAxisTuple(self.eventBlock.code)
        if hatCode is not None:
            # this is a hat
            self.processHat(hatCode, self.eventBlock.value)

        axesCode = findAxesAxisTuple(self.eventBlock.code)
        if axesCode is not None:
            self.processAxes(axesCode, self.eventBlock.value)

        self.eventBlock = None

    def run(self):
        if self.joyDev is None:
            print "Cannot start Joystick"
            return

        for event in self.joyDev.read_loop():
            if self.killMe:
                return

            self.eventBlock = event
            self.process_events()

    def stop(self):
        self.killMe = True
        time.sleep(0.1)
        try:
            self.joyDev.ungrab()
        except:
            pass



class JoyEvdevUIEventGenerator(JoyEvdev):

    event_right = PySide.QtCore.Signal()
    event_left = PySide.QtCore.Signal()
    event_up = PySide.QtCore.Signal()
    event_down = PySide.QtCore.Signal()

    event_select = PySide.QtCore.Signal()
    event_ok = PySide.QtCore.Signal()
    event_cancel = PySide.QtCore.Signal()


    def __init__(self):

        JoyEvdev.__init__(self)

        self.BUTTON_OK = pycnc_config.JOY_BUTTONS[pycnc_config.BTN_OK]
        self.BUTTON_SELECT = pycnc_config.JOY_BUTTONS[pycnc_config.BTN_SELECT]
        self.BUTTON_CANCEL = pycnc_config.JOY_BUTTONS[pycnc_config.BTN_CANCEL]

    def processButton(self, btnCode, value):
        if value != self.BUTTON_DOWN:
            return
        print "Button event"
        if btnCode == self.BUTTON_OK:
            self.event_ok.emit()
        elif btnCode == self.BUTTON_CANCEL:
            self.event_cancel.emit()
        elif btnCode == self.BUTTON_SELECT:
            self.event_select.emit()

    def processHat(self, hatCode, value):

        if hatCode in pycnc_config.JOY_XAXIS_MAP['hats']:
            # this is a X hat movement
            direction = value * pycnc_config.JOY_XAXIS_MAP['hatsMult'][
                pycnc_config.JOY_XAXIS_MAP['hats'].index(hatCode)]
            if direction > 0:
                self.event_right.emit()
            elif direction < 0:
                self.event_left.emit()
        elif hatCode in pycnc_config.JOY_YAXIS_MAP['hats']:
            # this is a X hat movement
            direction = value * pycnc_config.JOY_YAXIS_MAP['hatsMult'][
                pycnc_config.JOY_YAXIS_MAP['hats'].index(hatCode)]
            if direction > 0:
                self.event_down.emit()
            elif direction < 0:
                self.event_up.emit()



