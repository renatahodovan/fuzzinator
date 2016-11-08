# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from urwid import *

from .decor_widgets import PatternBox
from .graphics import fz_box_pattern
from .button import FormattedButton


class Dialog(PopUpTarget):
    signals = ['close']

    def __init__(self, title, body, footer_btns, warning=False):
        if not warning:
            style = dict(body='dialog', title='dialog_title', border='dialog_border')
        else:
            style = dict(body='warning', title='warning_title', border='warning_border')

        self.walker = SimpleListWalker(body)
        self.listbox = ListBox(self.walker)
        self.frame = Frame(body=AttrMap(self.listbox, style['body']),
                           footer=Columns([('pack', btn) for btn in footer_btns], dividechars=1),
                           focus_part='body')
        super(Dialog, self).__init__(AttrMap(PatternBox(self.frame, title=(style['title'], title), **fz_box_pattern()),
                                             attr_map=style['border']))

    def keypress(self, size, key):
        if key in ['esc']:
            self._emit('close')
        elif key in ['tab']:
            if self.frame.focus_part == 'body':
                try:
                    next_pos = self.walker.next_position(self.listbox.focus_position)
                    self.listbox.focus_position = next_pos
                except IndexError:
                    self.frame.focus_part = 'footer'
                    self.frame.footer.focus_col = 0
            elif self.frame.footer and self.frame.footer.contents:
                if self.frame.footer.focus_col < len(self.frame.footer.contents) - 1:
                    self.frame.footer.focus_col += 1
                else:
                    self.frame.focus_part = 'body'
                    self.listbox.focus_position = 0
        else:
            super(Dialog, self).keypress(size, key)


class WarningDialog(Dialog):
    def __init__(self, msg):
        super(WarningDialog, self).__init__(title='WARNING',
                                            body=[Text(msg)],
                                            footer_btns=[FormattedButton('Close', lambda button: self._emit('close'))],
                                            warning=True)


class FormattedIssueDialog(Dialog):
    def __init__(self, issue, tracker):
        super(FormattedIssueDialog, self).__init__(title=issue['id'],
                                                   body=[Padding(Text(line, wrap='clip'), left=2, right=2) for line in tracker.format_issue(issue).splitlines()],
                                                   footer_btns=[FormattedButton('Close', lambda button: self._emit('close'))])


class EditIssueDialog(Dialog):
    def __init__(self, issue, db):
        self.issue = issue
        self.db = db

        self.edit_boxes = dict()
        rows = []
        for prop in issue:
            if prop == '_id':
                continue
            self.edit_boxes[prop] = Edit('', str(issue[prop]), multiline=True)
            rows.append(Columns([('weight', 1, Text(('dialog_secondary', prop + ': '))),
                                 ('weight', 10, self.edit_boxes[prop])], dividechars=1))

        super(EditIssueDialog, self).__init__(title=issue['id'],
                                              body=rows,
                                              footer_btns=[FormattedButton('Save', self.save_modifications),
                                                           FormattedButton('Close', lambda button: self._emit('close'))])

    def save_modifications(self, btn):
        updated = dict()
        for prop, box in self.edit_boxes.items():
            updated[prop] = box.edit_text.encode('utf-8', errors='ignore')
        self.db.update_issue(self.issue, updated)
        self._emit('close')
