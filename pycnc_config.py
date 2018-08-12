from PySide.QtCore import Qt

# GrblWriter

SERIAL_PATTERN="/dev/ttyACM*"
BAUD=115200
SERIAL_DEBUG = True # define if serial communication should be shown
CHECK_GCODE = True # define if every new GCode file should be run in check mode first

# filelist
# patterns for gcode files
GCODE_PATTERN = ['.*\.nc', '.*\.ngc', '.*\.gc', '.*\.gcode']
EXTRA_MOUNTPOINTS = [] # extra directories to show in the file list dialog

# GCode options
# unsupported gcode to silently remove
SUPPRESS_GCODE = []

# enabled joggers. If a jogger is not found, it is anyway disregarded. Should be safe leaving them on true
JOG_KEYBOARD_ENABLED = True
JOG_JOYPAD_ENABLED = True
JOG_SHUTTLE_ENABLED = True


# standard feed rates used for jogging the machine
STD_FEED=2000
STD_FEED_Z=1000
MIN_FEED = 2000
MAX_FEED = 4000
MIN_FEED_Z = 1000
MAX_FEED_Z = 1000

# GCodeLoader
G0_FEED = 5000 # feed rate for G0. Default value that should get overwritten by the config

# JoyEventGenerator
BTN_REPEAT = 200 # repeat time for buttons in ms

#JoyFileList
# values for joystick buttons corresponding to actions in the filelist
HAT_RIGHT=0
HAT_LEFT=1
HAT_UP=2
HAT_DOWN=3
BTN_SELECT=0
BTN_OK=8
BTN_CANCEL=9

# JoyJogThread
BTN_ZERO=0
BTN_ZEROZ=1
BTN_HOME=2

# KeyboardJogger
KEY_XPOS = [Qt.Key_6]
KEY_XNEG = [Qt.Key_4]
KEY_YPOS = [Qt.Key_8]
KEY_YNEG = [Qt.Key_2]
KEY_ZPOS = [Qt.Key_9]
KEY_ZNEG = [Qt.Key_3]
KEY_SETHOME = [Qt.Key_0]
KEY_SETZ0 = [Qt.Key_Enter]
KEY_HOME = [Qt.Key_5]

# JoyStatus
# Mapping of joystick buttons and axes to movements.

JOY_XAXIS_MAP = {
  'axes' : [ 0, 3, (0,0), (1,0) ], # axis 0 and 3 move along x. 0 is left-right movement of left analog axis; 3 is right analog axis. Tuples correspond to evdev axis
  'axesMult' : [ 50, 5, 1, 0.1 ], # left axis moves maximum of 50, right axis of 5
  'hats' : [ (0,0) ], # hat 0 (the only one) axis 0 (left-right) moves by 1 on x axis
  'hatsMult' : [ 1 ],
  'btns' : [], # no buttons are mapped to x movement
  'btnsMult': []
}

JOY_YAXIS_MAP = {
  'axes' : [ 1, 2, (0,1), (1,1) ],
  'axesMult' : [ -50, -5, 1, 0.1 ],
  'hats' : [ (0,1) ],
  'hatsMult' : [ 1 ],
  'btns' : [],
  'btnsMult': []
}

JOY_ZAXIS_MAP = {
  'axes' : [],
  'axesMult' : [],
  'hats' : [],
  'hatsMult' : [],
  'btns' : [ 4, 5, 6, 7 ],
  'btnsMult' : [ 1, -1, 0.1, -0.1]
}

# Shuttle jogger
SHUTTLE_IDENTIFIER = 'ShuttleXpress' # how the system identifies the Shuttle
SHUTTLE_STEPSIZES = [0.1, 1.0, 10.0] # pressing button 5 changes step sizes of the dial
def SHUTTLE_WHEEL_TO_MOVEMENT_TRANSFORMATION(wheelValue): # this function defines how the wheel rotation is mapped to machine movement. This is simple 1:1. Might be quadratic or exponential?
  return wheelValue

# evdev codes for shuttle inputs. Don't change if you don't know what this is. Useful it you are not using the exact shuttlexpress. Use the evtest linux command
SHUTTLE_BUTTON_1 = 260
SHUTTLE_BUTTON_2 = 261
SHUTTLE_BUTTON_3 = 262
SHUTTLE_BUTTON_4 = 263
SHUTTLE_BUTTON_5 = 264

SHUTTLE_WHEEL = 8
SHUTTLE_DIAL = 7

# evdev codes for joystick
JOY_IDENTIFIER = 'Game Controller'
JOY_BUTTONS = [288, 289, 290, 291, 292, 293, 294, 295, 296, 297]
JOY_HATS = [[16,17]] # codes for each axis of each hat: [ [Hat0_X, Hat0_Y], [Hat1_X, Hat1_Y] ] etc...
JOY_AXES = [[0,1], [5,2]] # codes for each axis of each "axes" (analog joy)





# Probing
ENABLE_PROBING = True
PROBING_DISTANCE = 20 # maximum distance the probe should travel in the Z direction
PROBING_FEED = 10 # speed at which the probe should travel
PROBING_SPACING = 10 # spacing in the probe grid