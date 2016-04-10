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
  
import pycnc_config
  
class JoyStatus:
  def __init__(self):
    # Set up the joystick
    pygame.init()
    pygame.joystick.init()
    #print "Number of joysticks:", pygame.joystick.get_count()
    if pygame.joystick.get_count() == 0:
      print "No Joystick available"
      self.joystick = None
    else:
      self.joystick = pygame.joystick.Joystick(0)
      self.joystick.init()
      
  def getAxis(self, axis):
    if not self.joystick: return 0
    if axis < self.joystick.get_numaxes():
      return self.joystick.get_axis(axis)
    return 0
  
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
  
  def getMovement(self, axisDict):
    # check axes
    for joyAxisIndex in range(0,len(axisDict['axes'])):
      joyAxis = axisDict['axes'][joyAxisIndex]
      if self.getAxis(joyAxis) != 0:
        return self.getAxis(joyAxis)*axisDict['axesMult'][joyAxisIndex]
      
    # check hats
    for joyHatIndex in range(0,len(axisDict['hats'])):
      joyHat = axisDict['hats'][joyHatIndex]
      hatN = joyHat[0]
      hatVal = joyHat[1]
      value = self.getHat(hatN)[hatVal]
      if value != 0:
        return value*axisDict['hatsMult'][joyHatIndex]
      
    # check buttons
    for btnIndex in range(0,len(axisDict['btns'])):
      btn = axisDict['btns'][btnIndex]
      value = self.getButton(btn)
      if value != 0:
        return value*axisDict['btnsMult'][btnIndex]
    return 0

  def getXYZ(self):
    xMovement = self.getMovement(pycnc_config.JOY_XAXIS_MAP)
    yMovement = self.getMovement(pycnc_config.JOY_YAXIS_MAP)
    zMovement = self.getMovement(pycnc_config.JOY_ZAXIS_MAP)
    return (xMovement, yMovement, zMovement)
  
## main loop
if __name__ == '__main__':
  pygame.init()
  joy = JoyStatus()
  while (True):
    pygame.event.get()
    xyz = joy.getXYZ()
    if xyz != (0,0,0):
      print xyz
      
    time.sleep(0.1)
    
    
    
