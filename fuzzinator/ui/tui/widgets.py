# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pyperclip
import random
import time

from collections import OrderedDict
from math import ceil
from urwid import *

from fuzzinator.tracker.base import init_tracker
from fuzzinator.config import config_get_name_from_section
from .dialogs import FormattedButton, ViewButton, EditButton, ReportButton, WarningDialog
from .table import Table, TableColumn
from .decor_widgets import PatternBox
from .graphics import fz_box_pattern, fz_logo_4lines


class MainWindow(PopUpLauncher):
    signals = ['close', 'refresh', 'select', 'warning']

    def __init__(self, controller):
        self.controller = controller
        self.config = controller.config
        self.db = controller.db
        self.trackers = dict()

        self.logo = FuzzerLogo(max_load=controller.capacity)
        self.issues_table = IssuesTable(issues_baseline=[issue['_id'] for issue in self.db.all_issues()], db=self.db, initial_sort='id')
        self.stat_table = StatTable(['fuzzer'], stat_baseline=self.db.stat_snapshot([config_get_name_from_section(fuzz_section) for fuzz_section in controller.fuzzers]), db=self.db)
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
        self.footer_btns['help'] = FormattedButton('F1')
        self.footer_btns['menu'] = FormattedButton('F2')
        self.footer_btns['view'] = ViewButton('F3 View', self.issues_table, self.config, self.trackers)
        self.footer_btns['edit'] = EditButton('F4 Edit', self.issues_table)
        self.footer_btns['copy'] = FormattedButton('F5 Copy', on_press=lambda btn: self.copy_selected())
        self.footer_btns['reduce'] = FormattedButton('F6 Reduce', on_press=lambda btn: self.add_reduce_job())
        self.footer_btns['report'] = ReportButton('F7 Report', self.issues_table, self.config, self.trackers)
        self.footer_btns['delete'] = FormattedButton('F8 Delete')
        self.footer_btns['show'] = FormattedButton('F9 Show all', on_press=lambda btn: self.show_all(btn))
        self.footer_btns['quit'] = FormattedButton('F10 Quit', on_press=lambda btn: self._emit('close'))

        self.view = AttrMap(Frame(body=Pile([('fixed', 6, self.logo), self.content_columns]),
                                  footer=BoxAdapter(Filler(AttrMap(Columns(list(self.footer_btns.values()), dividechars=1), 'footer_button_bg')), height=1)),
                            'main_bg')
        super(MainWindow, self).__init__(self.view)

        connect_signal(self, 'warning', lambda _, msg: self.create_warning(msg))
        connect_signal(self.issues_table, 'select', lambda source, selection: self.formatted_issue_popup(selection[1]))
        connect_signal(self.issues_table, 'refresh', lambda source: self._emit('refresh'))
        connect_signal(self.stat_table, 'refresh', lambda source: self._emit('refresh'))

    def create_warning(self, msg):
        width = max([len(line) for line in msg.splitlines()] + [20])
        height = msg.count('\n') + 4
        cols, rows = os.get_terminal_size()

        self.get_pop_up_parameters = lambda: dict(left=max(cols // 2 - width // 2, 1),
                                                  top=max(rows // 2 - height // 2, 1),
                                                  overlay_width=width,
                                                  overlay_height=height)
        self.warning_msg = msg
        self.open_pop_up()

    def create_pop_up(self):
        pop_up = WarningDialog(self.warning_msg)
        connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up

    def add_reduce_job(self):
        if self.issues_table.selection:
            issue = self.issues_table.selection.data
            self.controller.add_reduce_job(issue=self.db.find_issue_by_id(issue['_id']))

    def copy_selected(self):
        # FIXME: why not:
        # issue = self.issues_table.selection.data
        # sut = issue['sut']
        if self.issues_table.selection:
            sut = self.issues_table.listbox.focus.data['sut']
            sut_section = 'sut.' + sut
            if sut not in self.trackers:
                self.trackers[sut] = init_tracker(self.config, sut_section, self.db)
            pyperclip.copy(self.trackers[sut].format_issue(self.db.find_issue_by_id(self.issues_table.selection.data['_id'])))

    def keypress(self, size, key):
        if key == 'tab':
            if self.content_columns.focus_position == 0:
                self.content_columns.focus_position = 1
            else:
                self.content_columns.focus_position = 0
        elif key == 'f1':
            self.footer_btns['help'].keypress((0, 0), 'enter')
        elif key == 'f2':
            self.footer_btns['menu'].keypress((0, 0), 'enter')
        elif key == 'f3':
            self.footer_btns['view'].keypress((0, 0), 'enter')
        elif key == 'f4':
            self.footer_btns['edit'].keypress((0, 0), 'enter')
        elif key == 'f5':
            self.footer_btns['copy'].keypress((0, 0), 'enter')
        elif key == 'f6':
            self.footer_btns['reduce'].keypress((0, 0), 'enter')
        elif key == 'f7':
            self.footer_btns['report'].keypress((0, 0), 'enter')
        elif key == 'f8':
            self.footer_btns['delete'].keypress((0, 0), 'enter')
        elif key == 'f9':
            self.footer_btns['show'].keypress((0, 0), 'enter')
        elif key in ('q', 'Q', 'f10'):
            raise ExitMainLoop()
        else:
            super(MainWindow, self).keypress(size, key)

    def show_all(self, btn):
        if btn.label == 'F9 Show all':
            btn.set_label('F9 Show less')
            self.issues_table.all_issues = True
            self.stat_table.show_current = False
            self.issues_table.show_all()
            self.stat_table.show_all()
        else:
            btn.set_label('F9 Show all')
            self.issues_table.all_issues = False
            self.stat_table.show_current = True
            self.issues_table.show_less()
            self.stat_table.show_less()


class IssuesTable(Table):
    all_issues = False
    key_columns = ['id']
    query_data = []
    title = 'ISSUES'

    columns = [
        TableColumn('sut', width=('weight', 1), label='SUT'),
        TableColumn('fuzzer', width=('weight', 1), label='Fuzzer'),
        TableColumn('id', width=('weight', 3), label='Issue ID')
    ]

    def __init__(self, issues_baseline, db, *args, **kwargs):
        self.issues_baseline = issues_baseline
        self.db = db
        super(IssuesTable, self).__init__(*args, **kwargs)

    def keypress(self, size, key):
        if key == "shift up":
            self.sort_by_column(reverse=True)
        elif key == "shift down":
            self.sort_by_column(reverse=False)
        elif key == "ctrl s":
            self.sort_by_column(toggle=True)
        elif key in ["delete", 'd']:
            if len(self):
                self.db.remove_issue_by_id(self[self.focus_position].data['_id'])
                del self[self.focus_position]
        elif key in ["r", "ctrl r"]:
            if self.all_issues:
                self.show_all()
            else:
                self.show_less()
        else:
            return super(IssuesTable, self).keypress(size, key)

    def format_names(self, data):
        for entry in data:
            if entry['fuzzer'].startswith('fuzz.'):
                entry['fuzzer'] = entry['fuzzer'][5:]
            elif entry['sut'].startswith('sut.'):
                entry['sut'] = entry['sut'][4:]
        return data

    def update(self):
        if self.all_issues:
            self.show_all()
        else:
            self.show_less()

    def show_all(self):
        self.query_data = self.format_names(self.db.all_issues())
        self.requery(self.query_data)
        self.walker._modified()

    def show_less(self):
        current_issues = [issue for issue in self.db.all_issues() if issue['_id'] not in self.issues_baseline]
        self.query_data = self.format_names(current_issues)
        self.requery(self.query_data)
        self.walker._modified()

    def add_row(self, data, position=None, attr_map=None, focus_map=None):
        if 'reported' in data and data['reported']:
            attr_map = {None: 'table_row_reported'}
            focus_map = {None: 'table_row_reported focused'}
        elif 'reduced' in data and data['reduced']:
            attr_map = {None: 'table_row_reduced'}
            focus_map = {None: 'table_row_reduced focused'}
        return super(IssuesTable, self).add_row(data, position=0, attr_map=attr_map, focus_map=focus_map)


class StatTable(Table):

    columns = [
        TableColumn('fuzzer', width=('weight', 3), label='Fuzzer'),
        TableColumn('crashes', width=('weight', 1), label='Crashes'),
        TableColumn('unique', width=('weight', 1), label='Unique'),
        TableColumn('exec', width=('weight', 1), label='Exec')
    ]

    query_data = []
    title = 'STATISTICS'

    def __init__(self, key_columns, stat_baseline, db, *args, **kwargs):
        self.key_columns = key_columns
        self.stat_baseline = stat_baseline
        self.db = db
        self.show_current = True
        super(StatTable, self).__init__(*args, **kwargs)

    def update(self):
        if self.show_current:
            self.show_less()
        else:
            self.show_all()

    def show_all(self):
        self.query_data = list(self.db.stat_snapshot(None).values())
        self.requery(self.query_data)
        self.walker._modified()

    def show_less(self):
        snapshot = self.db.stat_snapshot([fuzzer for fuzzer in self.stat_baseline])
        current_progress = dict((fuzzer, dict(fuzzer=fuzzer,
                                              exec=snapshot[fuzzer]['exec'] - self.stat_baseline[fuzzer]['exec'],
                                              crashes=snapshot[fuzzer]['crashes'] - self.stat_baseline[fuzzer]['crashes'],
                                              unique=snapshot[fuzzer]['unique'] - self.stat_baseline[fuzzer]['unique'], )) for fuzzer in self.stat_baseline)
        self.query_data = list(current_progress.values())
        self.requery(self.query_data)
        self.walker._modified()


class JobsTable(WidgetWrap):
    _selectable = False

    def __init__(self):
        self.jobs = dict()
        self.title_text = 'JOBS (0)'
        self.walker = SimpleListWalker([])
        self.listbox = ListBox(self.walker)
        self.pattern_box = PatternBox(self.listbox, title=self.title, **fz_box_pattern())
        super(JobsTable, self).__init__(self.pattern_box)

    @property
    def title(self):
        return ['[', ('yellow', ' {txt} '.format(txt=self.title_text)), ']']

    @title.setter
    def title(self, value):
        self.pattern_box.set_title(['[', ('yellow', ' JOBS ({cnt}) '.format(cnt=value)), ']'])

    @property
    def active_jobs(self):
        return len(list(filter(lambda job: job.active, self.walker)))

    def insert_widget(self, ident, widget):
        self.jobs[ident] = widget
        self.walker.insert(0, self.jobs[ident])
        self.title = self.active_jobs

        if len(self.walker) == 1:
            self.listbox.focus_position = 0

    def add_fuzz_job(self, ident, fuzzer, sut, cost, batch):
        self.insert_widget(ident, FuzzerJobWidget(dict(fuzzer=fuzzer, sut=sut, cost=cost), pb_done=batch))

    def add_reduce_job(self, ident, sut, cost, issue_id, size):
        self.insert_widget(ident, ReduceJobWidget(data=dict(sut=sut, cost=cost, issue=issue_id), pb_done=size))

    def add_update_job(self, ident, sut):
        self.insert_widget(ident, UpdateJobWidget(dict(sut=sut)))

    def activate_job(self, ident):
        idx = self.walker.index(self.jobs[ident])
        self.walker[idx].activate()
        self.title = self.active_jobs

    def remove_job(self, ident):
        self.walker.remove(self.jobs[ident])
        del self.jobs[ident]
        self.title = self.active_jobs

    def job_progress(self, ident, progress):
        idx = self.walker.index(self.jobs[ident])
        self.walker[idx].update_progress(progress)

    def keypress(self, size, key):
        if not self.listbox.body:
            return

        if key == 'down':
            if self.listbox.focus_position < len(self.listbox.body) - 1:
                self.listbox.focus_position += 1
        elif key == 'up':
            if self.listbox.focus_position > 0:
                self.listbox.focus_position -= 1


class JobWidget(WidgetWrap):

    active = False
    _selectable = True

    inactive_map = {
        None: 'inactive_job',
        'progress_normal': 'inactive_job_progress_normal',
        'prop_name': 'inactive_job_prop',
        'prop_value': 'inactive_job_prop_value',
        'title_txt': 'inactive_job_title',
        'title_bg': 'inactive_job_title_bg'
    }

    inactive_focus_map = {
        None: 'inactive_job focused',
        'progress_normal': 'inactive_job_progress_normal focused',
        'progress_done': 'inactive_job_progress_done focused',
        'prop_name': 'inactive_job_prop focused',
        'prop_value': 'inactive_job_prop_value focused',
        'title_txt': 'inactive_job_title',
        'title_bg': 'inactive_job_title_bg'
    }

    active_map = {
        None: 'active_job',
        'progress_normal': 'active_job_progress_normal',
        'progress_done': 'active_job_progress_done',
        'progress_smooth': 'active_job_progress_smooth',
        'prop_name': 'active_job_prop',
        'prop_value': 'active_job_prop_value',
        'title_txt': 'active_job_title',
        'title_bg': 'active_job_title_bg'
    }

    active_focus_map = {
        None: 'active_job focused',
        'progress_normal': 'active_job_progress_normal focused',
        'progress_done': 'active_job_progress_done focused',
        'progress_smooth': 'active_job_progress_smooth focused',
        'prop_name': 'active_job_prop focused',
        'prop_value': 'active_job_prop_value focused',
        'title_txt': 'active_job_title focused',
        'title_bg': 'active_job_title_bg focused'
    }

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

        list_ui = [Columns([('weight', 3, Text(('prop_name', self.labels[x]))),
                            ('weight', 7, self.values[x])]) for x in data if x in self.labels]

        self.max_progress = None
        if pb_done is not None:
            self.max_progress = pb_done
            self.progress = ProgressBar('progress_normal', 'progress_done', current=0, done=self.max_progress, satt='progress_smooth')
            list_ui.append(Columns([('weight', 3, Text(('prop_name', 'Progress'))),
                                    ('weight', 7, self.progress)]))

        body = Pile([AttrMap(Text(('title_txt', self.title), align='center'), attr_map='title_bg'), *list_ui])
        self.attr = AttrMap(body, attr_map=self.inactive_map, focus_map=self.inactive_focus_map)
        super(JobWidget, self).__init__(self.attr)

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


class ReduceJobWidget(JobWidget):

    labels = dict(sut='Sut', cost='Cost', issue='Issue', size='Size')
    title = 'Reduce Job'
    height = 8

    def __init__(self, data, pb_done=None):
        super(ReduceJobWidget, self).__init__(data, pb_done)
        self.progress.set_completion(pb_done)


class UpdateJobWidget(JobWidget):

    labels = dict(sut='Sut', cost='Cost')
    title = 'Update Job'


class FuzzerLogo(WidgetWrap):

    def __init__(self, max_load=100):
        self.timer = TimerWidget('Uptime')
        self.load = ProgressBar('progress_normal', 'progress_complete', current=0, done=max_load)
        self.text = Text(fz_logo_4lines(), align='center')
        rows = Pile([('pack', self.text),
                     Columns([Filler(self.timer),
                              Filler(Text(('timer_label', 'Load: '), align='right')), Filler(self.load)], dividechars=1)])
        self.do_animate = False
        super(FuzzerLogo, self).__init__(rows)

    def random_color(self):
        return random.choice(['red', 'yellow', 'green', 'blue'])

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
        self.text.set_text(('green', fz_logo_4lines()))


class TimerWidget(Text):

    def __init__(self, label, no_ds=False):
        self.label = label
        self._started = time.time()
        self.no_ds = no_ds
        self.fmt = '%s: %02d:%02d:%02d' if self.no_ds else '%s: %02d:%02d:%04.1f'
        super(TimerWidget, self).__init__(self.format_text(0))
        self.update()

    def to_hms(self, ss):
        hh = ss // 3600
        r = ss - hh * 3600
        mm = r // 60
        # truncate to first digit after decimal
        ss = (r - mm * 60)
        return hh, mm, ss

    def format_text(self, ss):
        return self.fmt % (self.label, *self.to_hms(ss))

    def update(self):
        self.set_text(('timer_value', self.format_text(time.time() - self._started)))
        return True
