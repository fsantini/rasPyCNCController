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

from PySide.QtCore import *
import pycnc_config
from AbstractJogger import AbstractJogger
import pycnc_config

class KeyboardJogger(AbstractJogger):

    def __init__(self):
        AbstractJogger.__init__(self)
        self.enabled = False

    def start(self):
        self.enabled = True

    def stop(self):
        self.enabled = False

    def install(self, widget):
        widget.installEventFilter(self)

    def eventFilter(self, widget, event):
        # if this is not enabled, just pass the events through
        if not self.enabled:
            return False

        if event.type() != QEvent.Type.KeyPress:
            return False

        k = event.key()

        if k in pycnc_config.KEY_XPOS:
            self.relative_move_event.emit([1, 0, 0], pycnc_config.MAX_FEED)
        elif k in pycnc_config.KEY_XNEG:
            self.relative_move_event.emit([-1, 0, 0], pycnc_config.MAX_FEED)
        elif k in pycnc_config.KEY_YPOS:
            self.relative_move_event.emit([0, 1, 0], pycnc_config.MAX_FEED)
        elif k in pycnc_config.KEY_YNEG:
            self.relative_move_event.emit([0, -1, 0], pycnc_config.MAX_FEED)
        elif k in pycnc_config.KEY_ZPOS:
            self.relative_move_event.emit([0, 0, 1], pycnc_config.MAX_FEED_Z)
        elif k in pycnc_config.KEY_ZNEG:
            self.relative_move_event.emit([0, 0, -1], pycnc_config.MAX_FEED_Z)
        elif k in pycnc_config.KEY_HOME:
            self.absolute_move_event.emit([0, 0, 0], None)
        elif k in pycnc_config.KEY_SETHOME:
            self.home_update_event.emit([0, 0, 0])
        elif k in pycnc_config.KEY_SETZ0:
            self.home_update_event.emit([None, None, 0])
        else:
            return False

        return True
