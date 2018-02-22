# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import json
import os
import pkgutil
import time
import sys

from multiprocessing import Lock, Process, Queue
from urwid import connect_signal, raw_display, util, ExitMainLoop, MainLoop, PopUpLauncher

from fuzzinator import Controller
from fuzzinator.ui import build_parser, process_args
from fuzzinator.config import config_get_name_from_section
from .tui_listener import TuiListener
from .widgets import MainWindow


class Tui(PopUpLauncher):
    signals = ['close']

    def __init__(self, controller, style):
        # Shared objects to help event handling.
        self.events = Queue()
        self.lock = Lock()

        self.view = MainWindow(controller)
        self.screen = raw_display.Screen()
        self.screen.set_terminal_properties(256)

        self.loop = MainLoop(widget=self,
                             palette=style,
                             screen=self.screen,
                             unhandled_input=Tui.exit_handler,
                             pop_ups=True)

        self.pipe = self.loop.watch_pipe(self.update_ui)
        self.loop.set_alarm_in(0.1, Tui.update_timer, self.view.logo.timer)
        super(Tui, self).__init__(self.view)

        connect_signal(self.view.issues_table, 'refresh', lambda source: self.loop.draw_screen())
        connect_signal(self.view.stat_table, 'refresh', lambda source: self.loop.draw_screen())

    def update_ui(self, _):
        while True:
            try:
                event = self.events.get_nowait()
                if hasattr(self, event['fn']):
                    getattr(self, event['fn'])(**event['kwargs'])
            except:
                break

    def update_timer(self, timer):
        if timer.update():
            self.set_alarm_in(0.1, Tui.update_timer, timer)

    def new_fuzz_job(self, ident, fuzzer, sut, cost, batch):
        self.view.job_table.add_fuzz_job(ident, fuzzer, sut, cost, batch)

    def new_reduce_job(self, ident, sut, cost, issue_id, size):
        self.view.job_table.add_reduce_job(ident, sut, cost, issue_id, size)

    def new_update_job(self, ident, sut):
        self.view.job_table.add_update_job(ident, sut)

    def remove_job(self, ident):
        self.view.job_table.remove_job(ident)

    def activate_job(self, ident):
        self.view.job_table.activate_job(ident)

    def job_progress(self, ident, progress):
        self.view.job_table.job_progress(ident, progress)

    def update_load(self, load):
        self.view.logo.load.set_completion(load)

    def update_fuzz_stat(self):
        self.view.stat_table.update()

    def new_issue(self, issue):
        issue['sut'] = config_get_name_from_section(issue['sut'])
        # Do shiny animation if a new issue has received.
        self.view.logo.do_animate = True
        self.loop.set_alarm_at(time.time() + 5, callback=self.view.logo.stop_animation)
        self.loop.set_alarm_in(0.1, self.view.logo.animate, self.view.logo)
        self.view.issues_table.add_row(issue)

    def invalid_issue(self, issue):
        self.view.remove_issue_popup(ident=issue['_id'])

    def update_issue(self, issue):
        self.view.issues_table.update_row(ident=issue['_id'])

    def warning(self, msg):
        self.view._emit('warning', msg)

    @staticmethod
    def exit_handler(key):
        if key in ('q', 'Q', 'f10'):
            raise ExitMainLoop()


def load_style(style):
    return [
        ('default',                     style['default_fg'],                style['default_bg']),
        ('logo',                        style['logo_fg'],                   style['default_bg']),
        ('logo_secondary',              style['logo_secondary_fg'],         style['default_bg']),
        ('logo_fireworks_1',            'yellow',                           style['default_bg']),
        ('logo_fireworks_2',            'light red',                        style['default_bg']),
        ('logo_fireworks_3',            'dark blue',                        style['default_bg']),
        ('logo_fireworks_4',            'light green',                      style['default_bg']),
        ('label',                       style['label_fg'],                  style['default_bg']),
        ('time',                        style['time_fg'],                   style['default_bg']),
        ('load_progress',               style['load_progress_fg'],          style['load_progress_bg']),
        ('load_progress_complete',      style['load_progress_complete_fg'], style['load_progress_complete_bg']),
        ('button',                      style['button_fg'],                 style['button_bg']),
        ('border',                      style['border_fg'],                 style['default_bg']),
        ('border_title',                style['border_title_fg'],           style['default_bg']),
        ('selected',                    style['default_fg'],                style['selected_bg']),
        ('table_head',                  style['table_head_fg'],             style['table_head_bg']),
        ('table_head_sorted',           style['table_head_sorted_fg'],      style['table_head_bg']),
        ('issue_reduced',               style['issue_reduced_fg'],          style['default_bg']),
        ('issue_reported',              style['issue_reported_fg'],         style['default_bg']),
        ('issue_reduced_selected',      style['issue_reduced_fg'],          style['selected_bg']),
        ('issue_reported_selected',     style['issue_reported_fg'],         style['selected_bg']),
        ('job_head',                    style['job_head_fg'],               style['job_head_bg']),
        ('job_label',                   style['job_label_fg'],              style['default_bg']),
        ('job_head_inactive',           style['job_head_inactive_fg'],      style['job_head_inactive_bg']),
        ('job_inactive',                style['job_inactive_fg'],           style['default_bg']),
        ('job_progress',                style['job_progress_fg'],           style['job_progress_bg']),
        ('job_progress_complete',       style['job_progress_complete_fg'],  style['job_progress_complete_bg']),
        ('job_progress_inactive',       style['default_bg'],                style['default_bg']),
        ('job_label_selected',          style['job_label_fg'],              style['selected_bg']),
        ('job_inactive_selected',       style['job_inactive_fg'],           style['selected_bg']),
        ('dialog',                      style['dialog_fg'],                 style['dialog_bg']),
        ('dialog_title',                style['dialog_title_fg'],           style['dialog_title_bg']),
        ('dialog_border',               style['dialog_border_fg'],          style['dialog_bg']),
        ('dialog_secondary',            style['dialog_secondary_fg'],       style['dialog_bg']),
        ('warning',                     style['warning_fg'],                style['warning_bg']),
        ('warning_title',               style['warning_title_fg'],          style['warning_title_bg']),
        ('warning_border',              style['warning_border_fg'],         style['default_bg']),
    ]


def execute(args=None, parser=None):
    parser = build_parser(parent=parser)
    parser.add_argument('--force-encoding', metavar='NAME', default=None, choices=['utf-8', 'ascii'],
                        help='force text encoding used for TUI widgets (%(choices)s; default: autodetect)')
    parser.add_argument('-U', dest='force_encoding', action='store_const', const='utf-8', default=argparse.SUPPRESS,
                        help='force UTF-8 encoding (alias for --force-encoding=%(const)s)')
    parser.add_argument('--log-file', metavar='FILE',
                        help='redirect stderr (instead of /dev/null; for debugging purposes)')
    parser.add_argument('-s', '--style', metavar='FILE',
                        help='alternative style file for TUI')
    arguments = parser.parse_args(args)
    process_args(arguments)

    # Redirect or suppress errors to spare tui from superfluous messages.
    if arguments.log_file:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(arguments.log_file, 'w')
    else:
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')

    if arguments.style:
        raw_style = json.load(arguments.style)
    else:
        raw_style = json.loads(pkgutil.get_data(__package__, os.path.join('resources', 'default_style.json')).decode(encoding='utf-8'))
    style = load_style(raw_style)

    if arguments.force_encoding:
        util.set_encoding(arguments.force_encoding)

    controller = Controller(config=arguments.config)
    tui = Tui(controller, style=style)
    controller.listener += TuiListener(tui.pipe, tui.events, tui.lock)
    fuzz_process = Process(target=controller.run, args=())

    try:
        fuzz_process.start()
        tui.loop.run()
    finally:
        Controller.kill_process_tree(fuzz_process.pid)
        raise ExitMainLoop()
