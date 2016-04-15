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

import fileinput
import re


class GCodeConverter:
  lastG = 'G0'
  lastX = 'X0'
  lastY = 'Y0'
  
  def __init__(self):
    pass
  
  def convert(self, line):
    line = line.strip().upper()
    if line.startswith('G'):
      self.lastG = line.split(' ')[0] # get the GCode
      #is there an X?
      xre = re.search('X[0-9.-]+', line)
      xfound = False
      if xre is not None:
        self.lastX = xre.group(0)
        xfound = True
      yre = re.search('Y[0-9.-]+', line)
      yfound = False
      if yre is not None:
        self.lastY = yre.group(0)
        yfound = True
        
      # there can't be an X without Y
      if xfound and not yfound:
        line += ' ' + self.lastY
      elif yfound and not xfound:
        line += ' ' + self.lastX
  
      return line
    elif line.startswith('X') or line.startswith('Y') or line.startswith('Z'):
      #is there an X?
      xre = re.search('X[0-9.-]+', line)
      xfound = False
      if xre is not None:
        self.lastX = xre.group(0)
        xfound = True
      yre = re.search('Y[0-9.-]+', line)
      yfound = False
      if yre is not None:
        self.lastY = yre.group(0)
        yfound = True
        
      # there can't be an X without Y
      if xfound and not yfound:
        line += ' ' + self.lastY
      elif yfound and not xfound:
        line += ' ' + self.lastX
  
      return self.lastG + ' ' + line
    else:
      return line
  

if __name__ == "__main__":
  conv = GCodeConverter()
  for line in fileinput.input():
    print conv.convert(line)
  