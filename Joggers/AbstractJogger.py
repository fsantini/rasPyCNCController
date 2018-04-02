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

# Abstract jogger class. In order to implement your own jogger, you need to derive this class.
# when the jogger is initialized, the install method will be called with a widget as a parameter. This can be used to catch Qt events.
# The jogger can have its own thread, it just needs to produce the following events (ALL COORDINATES ARE IN METRIC)
# relative_move_event((x,y,z), feed). If feed is None, a 60 move will be executed, otherwise a G1. x,y,z are the move offsets
# absolute_move_event((x,y,z), feed). If feed is None, a 60 move will be executed. Same as above, but absolute move. good for homing.
# home_update_event((x,y,z)). Sets the current coordinates as (x,y,z). If any of x, y or z are None, that coordinate is unchanged (use (None, None, 0) to set Z=0)
# exit_event(bool). Indicate that we want to exit the jogging. True means "OK" and False means "Cancel"
# error_event(exception). Indicate an error.
#
# start and stop should enable/disable the jogger
#
# Note: move events that are sent while the machine is moving will be discarded. There is no need to avoid firing multiple move events.
# in order to install a jogger, call the method installJogger of the jogwidget.

from PySide.QtCore import *

class AbstractJogger(QObject):

    relative_move_event = Signal(object,object) # a G0/G1 command
    absolute_move_event = Signal(object,object)
    home_update_event = Signal(object) # a G10 P0 L20 command. argument is the offset
    exit_event = Signal(object)
    error_event = Signal(object)

    def __init__(self):
        QObject.__init__(self)

    def start(self):
        pass

    def stop(self):
        pass

    def install(self, widget):
        pass
