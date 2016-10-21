# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

"""
Widgets to extend Urwid capabilities
"""

from urwid import *


class PatternHLine(Widget):
    _sizing = frozenset(['flow'])
    ignore_focus = True

    def __init__(self, pattern):
        super(PatternHLine, self).__init__()
        assert len(pattern) != 0
        self.pattern = pattern

    def _repr_words(self):
        return super(PatternHLine, self)._repr_words() + [repr(self.pattern)]

    def rows(self, size, focus=False):
        return 1

    def render(self, size, focus=False):
        (maxcol,) = size
        text, cs = apply_target_encoding((self.pattern * maxcol)[:maxcol])
        return TextCanvas([text], cs=[cs], maxcol=maxcol)


class PatternVLine(BoxWidget):
    _selectable = False
    ignore_focus = True

    def __init__(self, pattern):
        super(PatternVLine, self).__init__()
        assert len(pattern) != 0
        self.pattern = []
        self.cs = []
        for p in list(pattern):
            _p, _cs = apply_target_encoding(p)
            self.pattern.append(_p)
            self.cs.append(_cs)

    def _repr_words(self):
        return super(PatternVLine, self)._repr_words() + [repr(self.pattern)]

    def render(self, size, focus=False):
        maxcol, maxrow = size
        return TextCanvas((self.pattern * maxrow)[:maxrow], cs=(self.cs * maxrow)[:maxrow], maxcol=maxcol)


class PatternBox(WidgetDecoration, WidgetWrap):

    def __init__(self, original_widget, title="",
                 tlcorner=u'┌', tline=u'─', lline=u'│',
                 trcorner=u'┐', blcorner=u'└', rline=u'│',
                 bline=u'─', brcorner=u'┘'):
        tline, bline = PatternHLine(tline), PatternHLine(bline)
        lline, rline = PatternVLine(lline), PatternVLine(rline)
        tlcorner, trcorner = Text(tlcorner), Text(trcorner)
        blcorner, brcorner = Text(blcorner), Text(brcorner)

        self.title_widget = Text(title)
        self.tline_widget = Columns([
            tline,
            ('flow', self.title_widget),
            tline,
        ])

        top = Columns([
            ('fixed', 1, tlcorner),
            self.tline_widget,
            ('fixed', 1, trcorner),
        ])

        middle = Columns([
            ('fixed', 1, lline),
            original_widget,
            ('fixed', 1, rline),
        ], box_columns=[0, 2], focus_column=1)

        bottom = Columns([
            ('fixed', 1, blcorner),
            bline,
            ('fixed', 1, brcorner),
        ])

        pile = Pile([
            ('flow', top),
            middle,
            ('flow', bottom)
        ], focus_item=1)

        WidgetDecoration.__init__(self, original_widget)
        WidgetWrap.__init__(self, pile)

    def set_title(self, text):
        self.title_widget.set_text(text)
        self.tline_widget._invalidate()
