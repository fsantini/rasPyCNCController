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

import pygame
import time
from PySide.QtCore import QThread
import pycnc_config


def eAnd(list1, list2):
  return [ x&y for (x,y) in zip(list1, list2) ]

def eOr(list1, list2):
  return [ x|y for (x,y) in zip(list1, list2) ]

def eMinus(list1, list2):
  return [ (x-y if (x>0 and y>0) else 0) for (x,y) in zip(list1, list2) ]

class JoyEventGenerator(QThread):
  def __init__(self):
    QThread.__init__(self)
    self.killMe = False
    pygame.init()
    pygame.joystick.init()
    #print "Number of joysticks:", pygame.joystick.get_count()
    if pygame.joystick.get_count() == 0:
      print "No Joystick available"
      self.joystick = None
    else:
      self.joystick = pygame.joystick.Joystick(0)
      self.joystick.init()
      
  def getHat(self, hat):
    if not self.joystick: return 0      
    if hat < self.joystick.get_numhats():
      return self.joystick.get_hat(hat)
    return 0
  
  def getButton(self, btn):
    if not self.joystick: return 0
    if btn < self.joystick.get_numbuttons():
      return self.joystick.get_button(btn)
    return 0
  
  # returns a list with 4 logical elements: x+, x-, y+, y-
  def getHatTimes(self):
    t = time.time()
    hatVal = self.getHat(0)
    hatStat = []
    hatStat.append(t if (hatVal[0] == +1) else -1)
    hatStat.append(t if (hatVal[0] == -1) else -1)
    hatStat.append(t if (hatVal[1] == +1) else -1)
    hatStat.append(t if (hatVal[1] == -1) else -1)
    return hatStat
  
  def getButtonTimes(self):
    buttonStat = []
    t = time.time()
    for b in range(0, self.joystick.get_numbuttons()):
      buttonStat.append(t if (self.getButton(b) == 1) else -1)
    return buttonStat
  
  #reimplement these methods to do something useful
  def hatEvent(self, hEv):
    print "Hat event", hEv
    
  def btnEvent(self, bEv):
    print "Button event", bEv
  
  def run(self):
    if not self.joystick: return
    pygame.init()
    pygame.joystick.init()
    #if pygame.joystick.get_count() == 0: return
    self.joystick = pygame.joystick.Joystick(0)
    self.joystick.init()
    pygame.event.get()
    oldButtonTimes = self.getButtonTimes()
    oldHatTimes = self.getHatTimes()
    self.killMe = False
    while (not self.killMe):
      pygame.event.get()
      newButtonTimes = self.getButtonTimes()
      newHatTimes = self.getHatTimes()
      for btn in range(0, len(newButtonTimes)):
        oldTime = oldButtonTimes[btn]
        newTime = newButtonTimes[btn]
        if (oldTime < 0 ) and (newTime >= 0):
          # a button was clicked
          oldButtonTimes[btn] = newTime # set old button time to the new time, because the button was clicked now
          self.btnEvent(btn)
        elif (oldTime >= 0) and (newTime >= 0):
          if (newTime - oldTime)*1000 > pycnc_config.BTN_REPEAT:
            # fire the event and reset the counter
            oldButtonTimes[btn] = newTime # set old button time to the new time, because the event was fired
            self.btnEvent(btn)
        elif (newTime < 0):
          oldButtonTimes[btn] = -1 # the button was released
          
      for hat in range(0, len(newHatTimes)):
        oldTime = oldHatTimes[hat]
        newTime = newHatTimes[hat]
        if (oldTime < 0 ) and (newTime >= 0):
          # a button was clicked
          oldHatTimes[hat] = newTime # set old button time to the new time, because the button was clicked now
          self.hatEvent(hat)
        elif (oldTime >= 0) and (newTime >= 0):
          if (newTime - oldTime)*1000 > pycnc_config.BTN_REPEAT:
            # fire the event and reset the counter
            oldHatTimes[hat] = newTime # set old button time to the new time, because the event was fired
            self.hatEvent(hat)
        elif (newTime < 0):
          oldHatTimes[hat] = -1 # the button was released
      
      time.sleep(0.05) # sleep 5ms

  def stop(self):
    self.killMe = True


if __name__ == "__main__":
  joyEv = JoyEventGenerator()
  joyEv.start()
  print "press return to exit"
  raw_input()
  joyEv.stop()
   
    

