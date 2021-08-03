# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import random
import time

from collections import OrderedDict
from datetime import datetime
from math import ceil

import pyperclip

from urwid import *

from ...config import config_get_object
from ...formatter import JsonFormatter
from .button import FormattedButton
from .decor_widgets import PatternBox
from .dialogs import WarningDialog, YesNoDialog
from .graphics import fz_box_pattern, fz_logo_4lines
from .popup_buttons import AboutButton, EditButton, ReportButton, ViewButton
from .table import Table, TableColumn


class MainWindow(PopUpLauncher):
    signals = ['close', 'refresh', 'select', 'warning']

    def __init__(self, controller):
        self.controller = controller
        self.config = controller.config
        self.db = controller.db

        self.logo = FuzzerLogo(max_load=controller.capacity)
        self.issues_table = IssuesTable(session_start=self.controller.session_start, db=self.db, initial_sort='sut')
        self.stat_table = StatTable(['fuzzer'], session_start=self.controller.session_start, session_baseline=self.controller.session_baseline, db=self.db)
        self.job_table = JobsTable()

        self.data_tables = Pile([
            ('weight', 4, self.issues_table),
            ('weight', 2, self.stat_table)
        ])

        # Setup the boxes.
        self.content_columns = Columns([
            ('weight', 4, self.job_table),
            ('weight', 6, self.data_tables)
        ], dividechars=0)

        self.footer_btns = OrderedDict()
        self.footer_btns['about'] = AboutButton('F1 About')
        self.footer_btns['validate'] = FormattedButton('F2 Validate', on_press=lambda btn: self.add_validate_job())
        self.footer_btns['view'] = ViewButton('F3 View', self.issues_table, self.config)
        self.footer_btns['edit'] = EditButton('F4 Edit', self.issues_table)
        self.footer_btns['copy'] = FormattedButton('F5 Copy', on_press=lambda btn: self.copy_selected())
        self.footer_btns['reduce'] = FormattedButton('F6 Reduce', on_press=lambda btn: self.add_reduce_job())
        self.footer_btns['report'] = ReportButton('F7 Report', self.issues_table, self.config)
        self.footer_btns['delete'] = FormattedButton('F8 Delete')
        self.footer_btns['show'] = FormattedButton('F9 Show all', on_press=self.show_all)
        self.footer_btns['quit'] = FormattedButton('F10 Quit', on_press=lambda btn: self._emit('close'))

        self.pop_up = None
        self.pop_up_params = None

        self.view = AttrMap(Frame(body=Pile([('fixed', 6, self.logo), self.content_columns]),
                                  footer=BoxAdapter(Filler(AttrMap(Columns(list(self.footer_btns.values()), dividechars=1), 'default')), height=1)),
                            'border')
        super().__init__(self.view)

        connect_signal(self, 'warning', lambda _, msg: self.warning_popup(msg))
        connect_signal(self.issues_table, 'select', lambda source, selection: self.footer_btns['view'].keypress((0, 0), 'enter'))
        connect_signal(self.issues_table, 'refresh', lambda source: self._emit('refresh'))
        connect_signal(self.issues_table, 'delete', lambda source: self.remove_issue_popup())
        connect_signal(self.stat_table, 'refresh', lambda source: self._emit('refresh'))

    def init_popup(self, msg):
        width = max(max(len(line) for line in msg.splitlines()), 20)
        height = msg.count('\n') + 4
        cols, rows = os.get_terminal_size()
        self.pop_up_params = dict(left=max(cols // 2 - width // 2, 1),
                                  top=max(rows // 2 - height // 2, 1),
                                  overlay_width=width,
                                  overlay_height=height)
        return self.open_pop_up()

    def warning_popup(self, msg):
        self.pop_up = WarningDialog(msg)
        connect_signal(self.pop_up, 'close', lambda button: self.close_pop_up())
        self.init_popup(msg)

    def remove_issue_popup(self):
        issue_oid = self.issues_table.selection.data['_id']
        msg = 'Are you sure you want to delete this issue?'
        self.pop_up = YesNoDialog(msg)
        connect_signal(self.pop_up, 'yes', lambda button: self.remove_issue(issue_oid))
        connect_signal(self.pop_up, 'no', lambda button: self.close_pop_up())
        self.init_popup(msg)

    def remove_issue(self, issue_oid):
        self.db.remove_issue_by_oid(issue_oid)
        if issue_oid in self.issues_table.row_dict:
            del self.issues_table[self.issues_table.body.rows.index(self.issues_table.row_dict[issue_oid])]
        self.close_pop_up()

    def get_pop_up_parameters(self):
        return self.pop_up_params

    def create_pop_up(self):
        return self.pop_up

    def add_reduce_job(self):
        if self.issues_table.selection:
            issue = self.db.find_issue_by_oid(self.issues_table.selection.data['_id'])
            if not self.config.has_section('sut.' + issue['sut']):
                self.warning_popup(msg='{sut} is not defined.'.format(sut=issue['sut']))
            else:
                self.controller.add_reduce_job(issue)

    def reduce_all(self):
        self.controller.reduce_all()

    def add_validate_job(self):
        if self.issues_table.selection:
            issue = self.db.find_issue_by_oid(self.issues_table.selection.data['_id'])
            if not self.controller.add_validate_job(issue):
                self.warning_popup(msg='{sut} is not defined.'.format(sut=issue['sut']))

    def copy_selected(self, test_bytes=False):
        if self.issues_table.selection:
            issue = self.db.find_issue_by_oid(self.issues_table.selection.data['_id'])
            if test_bytes:
                pyperclip.copy(str(issue['test']))
            else:
                formatter = config_get_object(self.config, 'sut.' + issue['sut'], ['tui_formatter', 'formatter']) or JsonFormatter()
                pyperclip.copy(formatter(issue=issue))

    def keypress(self, size, key):
        if key == 'tab':
            if self.content_columns.focus_col == 0:
                self.content_columns.focus_col = 1
                self.data_tables.focus_item = 0
            else:
                if self.data_tables.focus_position == 0:
                    self.data_tables.focus_position = 1
                else:
                    self.content_columns.focus_col = 0
            return None
        if key == 'f1':
            self.footer_btns['about'].keypress((0, 0), 'enter')
            return None
        if key == 'f2':
            self.footer_btns['validate'].keypress((0, 0), 'enter')
            return None
        if key == 'f3':
            self.footer_btns['view'].keypress((0, 0), 'enter')
            return None
        if key == 'f4':
            self.footer_btns['edit'].keypress((0, 0), 'enter')
            return None
        if key == 'f5':
            self.footer_btns['copy'].keypress((0, 0), 'enter')
            return None
        if key == 'shift f5':
            # Copy the test content as bytes to the clipboard.
            self.copy_selected(test_bytes=True)
            return None
        if key == 'f6':
            self.footer_btns['reduce'].keypress((0, 0), 'enter')
            return None
        if key == 'shift f6':
            self.reduce_all()
            return None
        if key == 'f7':
            self.footer_btns['report'].keypress((0, 0), 'enter')
            return None
        if key == 'f8':
            self.footer_btns['delete'].keypress((0, 0), 'enter')
            return None
        if key == 'f9':
            self.footer_btns['show'].keypress((0, 0), 'enter')
            return None
        if key == 'shift f9':
            self.issues_table.invert_invalid()
            return None
        if key in ('q', 'Q', 'f10'):
            raise ExitMainLoop()
        return super().keypress(size, key)

    def show_all(self, btn):
        if btn.label == 'F9 Show all':
            btn.set_label('F9 Show less')
            self.issues_table.update(show_all=True)
            self.stat_table.show_all()
        else:
            btn.set_label('F9 Show all')
            self.issues_table.update(show_all=False)
            self.stat_table.show_less()


class IssuesTable(Table):
    all_issues = False
    show_invalid = False
    key_columns = ['id']
    query_data = []
    title = 'ISSUES'

    columns = [
        TableColumn('sut', width=('weight', 1), label='SUT'),
        TableColumn('fuzzer', width=('weight', 1), label='Fuzzer'),
        TableColumn('id', width=('weight', 3), label='Issue ID')
    ]

    def __init__(self, session_start, db, *args, **kwargs):
        self.session_start = session_start
        self.db = db
        super().__init__(*args, **kwargs)

    def keypress(self, size, key):
        if key == 'shift up':
            self.sort_by_column(reverse=True)
            return None
        if key == 'shift down':
            self.sort_by_column(reverse=False)
            return None
        if key == 'ctrl s':
            self.sort_by_column(toggle=True)
            return None
        if key in ['delete', 'd']:
            if self:    # len(self) != 0
                issue_oid = self[self.focus_position].data['_id']
                self.db.update_issue_by_oid(issue_oid, {'invalid': datetime.utcnow()})
                self.invalidate_row(issue_oid)
            return None
        if key in ['shift delete', 'D']:
            if self:    # len(self) != 0
                self._emit('delete')
            return None
        if key in ['r', 'ctrl r']:
            self._emit('refresh')
            return None
        return super().keypress(size, key)

    def invalidate_row(self, issue_oid):
        if self.show_invalid:
            self.update_row(issue_oid=issue_oid)
        else:
            del self[self.body.rows.index(self.row_dict[issue_oid])]

    def invert_invalid(self):
        self.show_invalid = not self.show_invalid
        self.update(self.all_issues)

    def update(self, show_all):
        self.all_issues = show_all
        self.query_data = self.db.get_issues(include_invalid=self.show_invalid, session_start=None if self.all_issues else self.session_start)
        self.requery(self.query_data)
        self.walker._modified()

    def update_row(self, issue_oid):
        issue = self.db.find_issue_by_oid(issue_oid)
        attr_map, focus_map = self.get_attr(issue)
        super().update_row_style(issue_oid, attr_map, focus_map)

    def get_attr(self, data):
        if data.get('invalid'):
            attr_map = {None: 'issue_invalid'}
            focus_map = {None: 'issue_invalid_selected'}
        elif data.get('reported'):
            attr_map = {None: 'issue_reported'}
            focus_map = {None: 'issue_reported_selected'}
        elif data.get('reduced') is not None:
            attr_map = {None: 'issue_reduced'}
            focus_map = {None: 'issue_reduced_selected'}
        else:
            attr_map = {None: 'default'}
            focus_map = {None: 'selected'}
        return attr_map, focus_map

    def add_row(self, data, position=None, attr_map=None, focus_map=None):
        attr_map, focus_map = self.get_attr(data)
        return super().add_row(data, position=0, attr_map=attr_map, focus_map=focus_map)


class StatTable(Table):

    columns = [
        TableColumn('fuzzer', width=('weight', 3), label='Fuzzer'),
        TableColumn('issues', width=('weight', 1), label='Issues'),
        TableColumn('unique', width=('weight', 1), label='Unique'),
        TableColumn('exec', width=('weight', 1), label='Exec')
    ]

    query_data = []
    title = 'STATISTICS'

    def __init__(self, key_columns, session_start, session_baseline, db, *args, **kwargs):
        self.key_columns = key_columns
        self.session_start = session_start
        self.session_baseline = session_baseline
        self.db = db
        self.show_current = True
        super().__init__(*args, **kwargs)

    def update(self):
        if self.show_current:
            self.show_less()
        else:
            self.show_all()

    def show_all(self):
        self.show_current = False
        self.query_data = self.db.get_stats()
        self.requery(self.query_data)
        self.walker._modified()

    def show_less(self):
        self.show_current = True
        self.query_data = self.db.get_stats(session_start=self.session_start, session_baseline=self.session_baseline)
        self.requery(self.query_data)
        self.walker._modified()


class JobsTable(WidgetWrap):
    signals = ['click']

    _selectable = False

    def __init__(self):
        self.jobs = dict()
        self.title_text = 'JOBS (0)'
        self.walker = SimpleListWalker([])
        self.listbox = ListBox(self.walker)
        self.pattern_box = PatternBox(self.listbox, title=self.title, **fz_box_pattern())
        super().__init__(self.pattern_box)

    @property
    def title(self):
        return ['[', ('border_title', ' {txt} '.format(txt=self.title_text)), ']']

    @title.setter
    def title(self, value):
        self.pattern_box.set_title(['[', ('border_title', ' JOBS ({cnt}) '.format(cnt=value)), ']'])

    @property
    def active_jobs(self):
        return len(list(filter(lambda job: job.active, self.walker)))

    def insert_widget(self, job_id, widget):
        self.jobs[job_id] = widget
        self.walker.insert(0, self.jobs[job_id])
        self.title = self.active_jobs

        if len(self.walker) == 1:
            self.listbox.focus_position = 0

    def on_fuzz_job_added(self, job_id, fuzzer, sut, cost, batch):
        self.insert_widget(job_id, FuzzerJobWidget(dict(fuzzer=fuzzer, sut=sut, cost=cost), pb_done=batch))

    def on_reduce_job_added(self, job_id, sut, cost, issue_id, size):
        self.insert_widget(job_id, ReduceJobWidget(dict(sut=sut, cost=cost, issue=issue_id), pb_done=size))

    def on_update_job_added(self, job_id, sut):
        self.insert_widget(job_id, UpdateJobWidget(dict(sut=sut)))

    def on_validate_job_added(self, job_id, sut, issue_id):
        self.insert_widget(job_id, ValidateJobWidget(dict(sut=sut, issue=issue_id)))

    def on_job_activated(self, job_id):
        idx = self.walker.index(self.jobs[job_id])
        self.walker[idx].activate()
        self.title = self.active_jobs

    def on_job_removed(self, job_id):
        self.walker.remove(self.jobs[job_id])
        del self.jobs[job_id]
        self.title = self.active_jobs

    def on_job_progressed(self, job_id, progress):
        idx = self.walker.index(self.jobs[job_id])
        self.walker[idx].update_progress(progress)

    def keypress(self, size, key):
        if key == 'down':
            if self.listbox.body and self.listbox.focus_position < len(self.listbox.body) - 1:
                self.listbox.focus_position += 1
            return None
        if key == 'up':
            if self.listbox.body and self.listbox.focus_position > 0:
                self.listbox.focus_position -= 1
            return None
        return super().keypress(size, key)

    # Override the mouse_event method (param list is fixed).
    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            emit_signal(self, 'click')


class JobWidget(WidgetWrap):

    active = False
    _selectable = True

    inactive_map = {
        None: 'default',
        'prop_name': 'job_inactive',
        'prop_value': 'job_inactive',
        'header': 'job_head_inactive',
        'progress_normal': 'job_progress_inactive'
    }

    inactive_focus_map = dict(inactive_map)
    inactive_focus_map.update({
        None: 'selected',
        'prop_name': 'job_inactive_selected',
        'prop_value': 'job_inactive_selected'
    })

    active_map = {
        None: 'default',
        'prop_name': 'job_label',
        'prop_value': 'default',
        'header': 'job_head',
        'progress_normal': 'job_progress',
        'progress_done': 'job_progress_complete',
    }
    active_focus_map = dict(active_map)
    active_focus_map.update({
        None: 'selected',
        'prop_name': 'job_label_selected',
        'prop_value': 'selected'
    })

    title = ''          # To be redefined by subclasses.
    labels = dict()     # To be redefined by subclasses.

    def __init__(self, data, pb_done=None):
        self.values = dict()
        for x in data:
            if isinstance(data[x], int):
                value = str(data[x])
            elif isinstance(data[x], bytes):
                value = data[x].decode('utf-8', errors='ignore')
            else:
                value = data[x]
            self.values[x] = Text(('prop_value', value))

        body_content = [AttrMap(Text(('header', self.title), align='center'), attr_map='header')]
        body_content.extend((Columns([('weight', 2, Text(('prop_name', self.labels[x]))),
                                      ('weight', 8, self.values[x])]) for x in data if x in self.labels))

        self.max_progress = None
        if pb_done is not None:
            self.max_progress = pb_done
            self.progress = ProgressBar('progress_normal', 'progress_done', current=0, done=self.max_progress)
            body_content.append(Columns([('weight', 2, Text(('prop_name', 'Progress'))),
                                         ('weight', 8, self.progress)]))
        else:
            self.max_progress = None
            self.progress = None

        self.attr = AttrMap(Pile(body_content), attr_map=self.inactive_map, focus_map=self.inactive_focus_map)
        super().__init__(self.attr)

    def update_progress(self, done):
        # Workaround for an urwid issue that happens if the progressbar displays value < 3%.
        if self.progress and done > ceil(self.max_progress / 100) * 3:
            self.progress.set_completion(current=done)

    def activate(self):
        self.active = True
        self.attr.set_attr_map(attr_map=self.active_map)
        self.attr.set_focus_map(focus_map=self.active_focus_map)

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press':
            self._emit('click')


class FuzzerJobWidget(JobWidget):

    labels = dict(fuzzer='Fuzzer', sut='Sut', cost='Cost')
    title = 'Fuzzer Job'

    def __init__(self, data, pb_done):
        super().__init__(data, pb_done)


class ReduceJobWidget(JobWidget):

    labels = dict(sut='Sut', cost='Cost', issue='Issue')
    title = 'Reduce Job'
    height = 8

    def __init__(self, data, pb_done):
        super().__init__(data, pb_done)
        self.progress.set_completion(pb_done)


class UpdateJobWidget(JobWidget):

    labels = dict(sut='Sut')
    title = 'Update Job'


class ValidateJobWidget(JobWidget):

    labels = dict(sut='Sut', issue='Issue')
    title = 'Validate Job'


class FuzzerLogo(WidgetWrap):

    def __init__(self, max_load=100):
        self.timer = TimerWidget()
        self.load = ProgressBar('load_progress', 'load_progress_complete', current=0, done=max_load)
        self.text = Text(fz_logo_4lines(), align='center')
        rows = Pile([('pack', self.text),
                     Columns([(20, Columns([Filler(Text(('label', 'Uptime: '), align='left')),
                                            Filler(self.timer)])),
                              ('weight', 1, Filler(Text(''))),
                              ('weight', 1, Columns([Filler(Text(('label', 'Load: '), align='right')),
                                                     Filler(self.load)]))
                              ], dividechars=1)])
        self.do_animate = False
        super().__init__(rows)

    def random_color(self):
        return random.choice(['logo_fireworks_1', 'logo_fireworks_2', 'logo_fireworks_3', 'logo_fireworks_4'])

    def update_colors(self):
        text = []
        for x in self.text.text:
            text.append((self.random_color(), x))
        self.text.set_text(text)
        if self.do_animate:
            return True
        self.reset()
        return False

    def animate(self, loop, logo):
        if self.update_colors():
            loop.set_alarm_in(0.1, self.animate, logo)

    def stop_animation(self, loop, logo):
        self.do_animate = False

    def reset(self):
        self.text.set_text(fz_logo_4lines())


class TimerWidget(Text):

    def __init__(self):
        self._started = time.time()
        super().__init__(self.format_text(0))
        self.update()

    def to_hms(self, ss):
        hh = ss // 3600
        r = ss - hh * 3600
        mm = r // 60
        # truncate to first digit after decimal
        ss = (r - mm * 60)
        return hh, mm, ss

    def format_text(self, ss):
        return '%02d:%02d:%04.1f' % self.to_hms(ss)

    def update(self):
        self.set_text(('time', self.format_text(time.time() - self._started)))
        return True
