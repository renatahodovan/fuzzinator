# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ast import literal_eval
from datetime import datetime

from urwid import *

from ...config import config_get_callable
from ...formatter import JsonFormatter
from ...pkgdata import __author__, __author_email__, __pkg_name__, __url__, __version__
from .button import FormattedButton
from .decor_widgets import PatternBox
from .graphics import fz_box_pattern


class Dialog(PopUpTarget):
    signals = ['close']
    exit_keys = ['esc']

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
        super().__init__(AttrMap(PatternBox(self.frame, title=(style['title'], title), **fz_box_pattern()),
                                 attr_map=style['border']))

    def keypress(self, size, key):
        if key in self.exit_keys:
            self._emit('close')
            return None
        if key in ['tab']:
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
            return None
        return super().keypress(size, key)


class AboutDialog(Dialog):
    exit_keys = ['esc', 'f1']

    def __init__(self, ):
        self.content = self.compile_about_data()
        super().__init__(title='About',
                         body=[Text(self.content)],
                         footer_btns=[FormattedButton('Close', lambda button: self._emit('close'))])

    def compile_about_data(self, prop_width=15):
        return '{name_prop}: {name}\n' \
               '{version_prop}: {version}\n' \
               '{authors_prop}: {authors}\n' \
               '{mail_prop}: {email}\n' \
               '{homepage_prop}: {homepage}\n'.format(name_prop='Name'.ljust(prop_width),
                                                      name=__pkg_name__,
                                                      version_prop='Version'.ljust(prop_width),
                                                      version=__version__,
                                                      authors_prop='Authors'.ljust(prop_width),
                                                      authors=__author__,
                                                      mail_prop='E-mail'.ljust(prop_width),
                                                      email=__author_email__,
                                                      homepage_prop='Homepage'.ljust(prop_width),
                                                      homepage=__url__)


class WarningDialog(Dialog):
    exit_keys = ['esc', 'enter']

    def __init__(self, msg):
        super().__init__(title='WARNING',
                         body=[Text(msg)],
                         footer_btns=[FormattedButton('Close', lambda button: self._emit('close'))],
                         warning=True)


class YesNoDialog(Dialog):
    signals = ['yes', 'no']

    def keypress(self, size, key):
        if key == 'enter':
            self._emit('yes')
            return None
        if key == 'esc':
            self._emit('no')
            return None
        return super().keypress(size, key)

    def __init__(self, msg):
        super().__init__(title='Question',
                         body=[Text(msg)],
                         footer_btns=[
                             FormattedButton('Yes', lambda button: self._emit('yes')),
                             FormattedButton('No', lambda button: self._emit('no'))],
                         warning=True)


class FormattedIssueDialog(Dialog):
    exit_keys = ['esc', 'f3']

    def __init__(self, config, issue, db):
        formatter = config_get_callable(config, 'sut.' + issue['sut'], ['tui_formatter', 'formatter'])[0] or JsonFormatter
        super().__init__(title=formatter(issue=issue, format='short'),
                         body=[Padding(Text(line, wrap='clip'), left=2, right=2) for line in formatter(issue=issue).splitlines()],
                         footer_btns=[FormattedButton('Close', lambda button: self._emit('close'))])


class BugEditor(Edit):

    def keypress(self, size, key):
        if key == 'ctrl k':
            lines = self._edit_text.splitlines(keepends=True)
            line_cnt = self._edit_text[:self.edit_pos].count('\n')
            before = ''.join(lines[:line_cnt])
            after = ''.join(lines[line_cnt + 1:]) if line_cnt + 1 < len(lines) else ''
            self.set_edit_text(before + after)
            self.set_edit_pos(len(before))
            return None
        return super().keypress(size, key)


class EditIssueDialog(Dialog):

    exit_keys = ['esc', 'f4']

    def __init__(self, issue, db):
        self.issue = issue
        self.db = db

        self.edit_boxes = dict()
        self.type_dict = dict()
        rows = []
        for prop in issue:
            if prop == '_id':
                continue

            self.edit_boxes[prop] = BugEditor('', self._to_str(prop, issue[prop]), multiline=True)
            rows.append(Columns([('weight', 1, Text(('dialog_secondary', prop + ': '))),
                                 ('weight', 10, self.edit_boxes[prop])], dividechars=1))

        super().__init__(title=issue['id'],
                         body=rows,
                         footer_btns=[FormattedButton('Save', self.save_modifications),
                                      FormattedButton('Close', lambda button: self._emit('close'))])

    def _to_str(self, prop, value):
        t = type(value)
        self.type_dict[prop] = t

        if t == str:
            return value
        if t == bytes:
            return value.decode('utf-8', errors='ignore')
        if t == datetime:
            return value.strftime('%Y-%m-%d %H:%M:%S')
        if value is None:
            self.type_dict[prop] = None
            return ''
        return str(value)

    def _from_str(self, prop, value):
        t = self.type_dict[prop]

        if t == str:
            return value
        if t == int:
            return int(value)
        if t == bytes:
            return value.encode('utf-8', errors='ignore')
        if t == datetime:
            return datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        if t is None:
            return value or None
        return literal_eval(value)

    def save_modifications(self, btn):
        updated = dict()
        for prop, box in self.edit_boxes.items():
            updated[prop] = self._from_str(prop, box.edit_text)
        self.db.update_issue(self.issue, updated)
        self._emit('close')
