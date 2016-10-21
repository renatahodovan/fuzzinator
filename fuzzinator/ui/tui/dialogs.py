# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from os import get_terminal_size
from urwid import *

from fuzzinator.tracker import BugzillaReport, GithubReport
from fuzzinator.tracker.base import init_tracker

from .decor_widgets import PatternBox
from .graphics import fz_box_pattern
from .reporter_dialogs import BugzillaReportDialog, GithubReportDialog


class FooterButton(Button):
    button_left = Text(' ')
    button_right = Text(' ')


class FormattedButton(WidgetWrap):
    signals = ['click']
    _selectable = True

    def __init__(self, label, on_press=None, user_data=None):
        self.text_len = len(label)
        self.btn = FooterButton(label, on_press, user_data)
        WidgetWrap.__init__(self, AttrMap(self.btn, 'footer_button'))
        connect_signal(self.btn, 'click', lambda btn: self._emit('click'))

    def sizing(self):
        return frozenset(['fixed'])

    def pack(self, size=None, focus=None):
        return self.text_len + 6, 1

    @property
    def label(self):
        return self.btn.label

    @label.setter
    def label(self, value):
        self.btn.set_label(value)


class WarningDialog(WidgetWrap):
    signals = ['close']

    def __init__(self, msg):
        close_button = FormattedButton('Close', lambda button: self._emit('close'))

        frame = Frame(body=AttrMap(ListBox(SimpleListWalker([Padding(Text(msg, wrap='clip'), left=2, right=2)])), 'table_header'),
                      footer=close_button,
                      focus_part='body')

        WidgetWrap.__init__(self, AttrMap(PatternBox(frame, title=('warning_dialog_title', 'WARNING'), **fz_box_pattern()), attr_map='yellow'))

    def keypress(self, _, key):
        if key in ['esc', 'enter']:
            self._emit('close')


class FullScreenPopupLauncher(PopUpLauncher):

    def get_pop_up_parameters(self):
        cols, rows = get_terminal_size()
        return {'left': cols // 2, 'top': rows // 2, 'overlay_width': cols, 'overlay_height': rows}


class ViewButton(FullScreenPopupLauncher):
    signals = ['click']

    def __init__(self, label, issues_table, config, trackers):
        super(ViewButton, self).__init__(FormattedButton(label))
        self.issues_table = issues_table
        self.config = config
        self.trackers = trackers
        self.pop_up_params = {'left': -40, 'top': -100, 'overlay_width': 200, 'overlay_height': 60}
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None

        sut = focus.data['sut']
        sut_section = 'sut.' + sut
        if sut not in self.trackers:
            self.trackers[sut] = init_tracker(self.config, sut_section, self.issues_table.db)
        pop_up = FormattedIssueDialog(issue=self.issues_table.db.find_issue_by_id(focus.data['_id']),
                                      tracker=self.trackers[sut])

        connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up


class FormattedIssueDialog(WidgetWrap):
    signals = ['close']

    def __init__(self, issue, tracker):
        close_button = FormattedButton('Close', lambda button: self._emit('close'))

        content = [Padding(Text(line, wrap='clip'), left=2, right=2) for line in tracker.format_issue(issue).splitlines()]
        self.lines = len(content)
        self.listbox = ListBox(SimpleListWalker(content))
        self.listbox.focus_position = 0
        frame = Frame(body=AttrMap(PatternBox(self.listbox, title=('dialog_title', issue['id']), **fz_box_pattern()), attr_map='table_header'),
                      footer=close_button,
                      focus_part='body')

        WidgetWrap.__init__(self, AttrMap(frame, attr_map='main_bg'))

    def keypress(self, _, key):
        if key in ['esc', 'f3']:
            self._emit('close')
        elif key == 'down':
            self.listbox.focus_position += min(len(self.listbox.body), self.lines - self.listbox.focus_position - 1)
        elif key == 'up':
            self.listbox.focus_position -= min(len(self.listbox.body), self.listbox.focus_position)


class EditButton(FullScreenPopupLauncher):
    signals = ['click']

    def __init__(self, label, issues_table):
        super(EditButton, self).__init__(FormattedButton(label))
        self.issues_table = issues_table
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None

        pop_up = EditIssueDialog(issue=self.issues_table.db.find_issue_by_id(focus.data['_id']),
                                 db=self.issues_table.db)
        connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up


class EditIssueDialog(WidgetWrap):
    signals = ['close']

    def __init__(self, issue, db):
        self.issue = issue
        self.db = db

        self.edit_boxes = dict()
        rows = []
        for prop in issue:
            if prop == '_id':
                continue
            self.edit_boxes[prop] = Edit('', str(issue[prop]), multiline=True)
            rows.append(Columns([('weight', 1, Text(prop + ': ')),
                                 ('weight', 10, self.edit_boxes[prop])], dividechars=1))

        close_button = FormattedButton('Close', lambda button: self._emit('close'))
        save_button = FormattedButton('Save', self.save_modifications)

        frame = Frame(body=AttrMap(ListBox(SimpleListWalker(rows)), 'table_header'),
                      footer=Columns([('pack', save_button), ('pack', close_button)], dividechars=2),
                      focus_part='body')
        WidgetWrap.__init__(self, PatternBox(frame, title=('dialog_title', issue['id']), **fz_box_pattern()))

    def save_modifications(self, btn):
        updated = dict()
        for prop, box in self.edit_boxes.items():
            updated[prop] = box.edit_text.encode('utf-8', errors='ignore')
        self.db.update_issue(self.issue, updated)
        self._emit('close')

    def keypress(self, size, key):
        if key in ['esc', 'f3']:
            self._emit('close')
        else:
            super(EditIssueDialog, self).keypress(size, key)


class LoginDialog(WidgetWrap):
    signals = ['close', 'login']

    def __init__(self):
        name = Edit(caption='Username: ', edit_text='')
        pwd = Edit(caption='Password: ', edit_text='', mask='*')
        self.walker = SimpleListWalker([name, pwd,
                                        Columns([('pack', FormattedButton('Login',
                                                                          on_press=self.send_credentials,
                                                                          user_data=(name, pwd))),
                                                 ('pack', FormattedButton('Cancel',
                                                                          on_press=lambda btn: self._emit('close')))],
                                                dividechars=3)])
        view = PatternBox(Frame(body=ListBox(self.walker)), title=('dialog_title', 'Login'), **fz_box_pattern())
        WidgetWrap.__init__(self, AttrMap(view, attr_map='main_bg'))

    def send_credentials(self, _, details):
        self._emit('login', details[0].edit_text, details[1].edit_text)
        self._emit('close')

    def keypress(self, size, key):
        if key == 'esc':
            self._emit('close')
        elif key == 'tab':
            self.walker.set_focus(self.get_next_position())
        else:
            self._w.keypress(size, key)

    def get_next_position(self):
        current = self.walker.get_focus()[1]
        if current == len(self.walker.contents) - 1:
            return 0
        else:
            return self.walker.get_next(current)[1]


class LoginFailedDialog(WidgetWrap):
    signals = ['close']

    def __init__(self):
        view = PatternBox(Frame(body=Filler(Padding(FormattedButton('Close', on_press=lambda btn: self._emit('close')), width=12))),
                          title=('dialog_title', 'Login failed!'), **fz_box_pattern())
        WidgetWrap.__init__(self, AttrMap(view, attr_map='main_bg'))


class ReportButton(FullScreenPopupLauncher):
    signals = ['click', 'login', 'login_fail']

    def __init__(self, label, issues_table, config, trackers):
        super(ReportButton, self).__init__(FormattedButton(label))
        self.issues_table = issues_table
        self.config = config
        self.trackers = trackers
        self.pop_up = None
        self.popup_type = None

        connect_signal(self.original_widget, 'click', lambda btn: self.open_custom_pop_up('report'))
        connect_signal(self, 'login_fail', lambda btn: self.open_custom_pop_up('login_fail'))

    def open_custom_pop_up(self, event_type):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None

        sut = focus.data['sut']
        sut_section = 'sut.' + sut
        if sut not in self.trackers:
            self.trackers[sut] = init_tracker(self.config, sut_section, self.issues_table.db)

        if event_type == 'report':
            if not self.trackers[sut].logged_in:
                self.popup_type = 'small'
                pop_up = LoginDialog()

                width, height = 70, 20
                cols, rows = get_terminal_size()
                # Override fullscreen parameters.
                self.get_pop_up_parameters = lambda: dict(left=max(cols // 2 - width // 2, 1),
                                                          top=max(rows // 2 - height // 2, 1),
                                                          overlay_width=width,
                                                          overlay_height=height)
                connect_signal(pop_up, 'login', lambda btn, username, pwd: self.login(btn, self.trackers[sut], username, pwd))
                connect_signal(pop_up, 'close', lambda btn: self.close_pop_up())
            else:
                self.popup_type = 'full'
                self.get_pop_up_parameters = super(ReportButton, self).get_pop_up_parameters
                issue_details = self.issues_table.db.find_issue_by_id(focus.data['_id'])
                if isinstance(self.trackers[sut], BugzillaReport):
                    pop_up = BugzillaReportDialog(issue=issue_details,
                                                  tracker=self.trackers[sut])
                elif isinstance(self.trackers[sut], GithubReport):
                    pop_up = GithubReportDialog(issue=issue_details,
                                                tracker=self.trackers[sut])
                else:
                    # If there is no reporter interface for the given tracker
                    # then we only display the formatted issue.
                    pop_up = FormattedIssueDialog(issue=issue_details, tracker=self.trackers[sut])
                connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        elif event_type == 'login_fail':
            self.popup_type = 'small'
            pop_up = LoginFailedDialog()
            connect_signal(pop_up, 'close', lambda button: self.close_pop_up())

        self.pop_up = pop_up
        self.open_pop_up()

    def create_pop_up(self):
        return self.pop_up

    def close_pop_up(self):
        super(ReportButton, self).close_pop_up()
        self.issues_table.walker._modified()

    def login(self, btn, tracker, username, pwd):
        result = tracker.login(username, pwd)
        if not result:
            emit_signal(self, 'login_fail', 'login_fail')
        else:
            self.open_custom_pop_up('report')
