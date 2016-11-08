# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from urwid import *


class ShortButton(Button):
    button_left = Text(' ')
    button_right = Text(' ')


class FormattedButton(WidgetWrap):
    signals = ['click']
    _selectable = True

    def __init__(self, label, on_press=None, user_data=None, style='button'):
        self.text_len = len(label)
        self.btn = ShortButton(label, on_press, user_data)
        super(FormattedButton, self).__init__(AttrMap(self.btn, style))
        connect_signal(self.btn, 'click', lambda btn: self._emit('click'))

    def sizing(self):
        return frozenset(['fixed'])

    def pack(self, size=None, focus=None):
        return self.text_len + 6, 1
