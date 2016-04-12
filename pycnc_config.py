# GrblWriter

SERIAL_PATTERN="/dev/ttyACM*"
BAUD=115200

# filelist
# patterns for gcode files
GCODE_PATTERN = ['.*\.nc', '.*\.ngc', '.*\.gc', '.*\.gcode']

# JoyJogThread: standard feed rates used for jogging the machine
STD_FEED=2000
STD_FEED_Z=1000

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

# JoyStatus
# Mapping of joystick buttons and axes to movements.

JOY_XAXIS_MAP = {
  'axes' : [ 0, 3 ], # axis 0 and 3 move along x. 0 is left-right movement of left analog axis; 3 is right analog axis
  'axesMult' : [ 50, 5 ], # left axis moves maximum of 50, right axis of 5
  'hats' : [ (0,0) ], # hat 0 (the only one) axis 0 (left-right) moves by 1 on x axis
  'hatsMult' : [ 1 ],
  'btns' : [], # no buttons are mapped to x movement
  'btnsMult': []
}

JOY_YAXIS_MAP = {
  'axes' : [ 1, 2 ],
  'axesMult' : [ -50, -5 ],
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