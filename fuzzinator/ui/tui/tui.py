# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import json
import logging
import os
import pkgutil
import signal
import sys
import time

from multiprocessing import Lock, Process, Queue

from urwid import connect_signal, ExitMainLoop, MainLoop, raw_display, util

from ... import Controller
from .. import build_parser, process_args
from .tui_listener import TuiListener
from .widgets import MainWindow

logger = logging.getLogger(__name__)


class Tui(object):
    signals = ['close']

    def __init__(self, controller, style):
        # Shared objects to help event handling.
        self.events = Queue()
        self.lock = Lock()

        self.view = MainWindow(controller)
        self.screen = raw_display.Screen()
        self.screen.set_terminal_properties(256)

        self.loop = MainLoop(widget=self.view,
                             palette=style,
                             screen=self.screen,
                             unhandled_input=Tui.exit_handler,
                             pop_ups=True)

        self.pipe = self.loop.watch_pipe(self.update_ui)
        self.loop.set_alarm_in(0.1, self.update_timer, self.view.logo.timer)

        connect_signal(self.view.issues_table, 'refresh', lambda source: self.loop.draw_screen())
        connect_signal(self.view.stat_table, 'refresh', lambda source: self.loop.draw_screen())

    def update_ui(self, _):
        while True:
            try:
                event = self.events.get_nowait()
                if hasattr(self, event['fn']):
                    getattr(self, event['fn'])(**event['kwargs'])
            except Exception:
                break

    def update_timer(self, loop, timer):
        if timer.update():
            loop.set_alarm_in(0.1, self.update_timer, timer)

    def on_fuzz_job_added(self, ident, cost, sut, fuzzer, batch):
        self.view.job_table.on_fuzz_job_added(ident, fuzzer, sut, cost, batch)

    def on_reduce_job_added(self, ident, cost, sut, issue_id, size):
        self.view.job_table.on_reduce_job_added(ident, sut, cost, issue_id, size)

    def on_update_job_added(self, ident, cost, sut):
        self.view.job_table.on_update_job_added(ident, sut)

    def on_validate_job_added(self, ident, cost, sut, issue_id):
        self.view.job_table.on_validate_job_added(ident, sut, issue_id)

    def on_job_removed(self, ident):
        self.view.job_table.on_job_removed(ident)

    def on_job_activated(self, ident):
        self.view.job_table.on_job_activated(ident)

    def on_job_progressed(self, ident, progress):
        self.view.job_table.on_job_progressed(ident, progress)

    def on_load_updated(self, load):
        self.view.logo.load.set_completion(load)

    def on_stats_updated(self):
        self.view.stat_table.update()

    def on_issue_added(self, ident, issue):
        # Do shiny animation if a new issue has received.
        self.view.logo.do_animate = True
        self.loop.set_alarm_at(time.time() + 5, callback=self.view.logo.stop_animation)
        self.loop.set_alarm_in(0.1, self.view.logo.animate, self.view.logo)
        self.view.issues_table.add_row(issue)

    def on_issue_invalidated(self, ident, issue):
        self.view.issues_table.invalidate_row(ident=issue['_id'])

    def on_issue_updated(self, ident, issue):
        self.view.issues_table.update_row(ident=issue['_id'])

    def on_issue_reduced(self, ident, issue):
        self.view.issues_table.update_row(ident=issue['_id'])

    def warning(self, ident, msg):
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
        ('issue_invalid',               style['issue_invalid_fg'],          style['default_bg']),
        ('issue_invalid_selected',      style['issue_invalid_fg'],          style['selected_bg']),
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
    parser.add_argument('--utf8', '--utf-8', dest='force_encoding', action='store_const', const='utf-8', default=argparse.SUPPRESS,
                        help='force UTF-8 encoding (alias for --force-encoding=%(const)s)')
    parser.add_argument('--log-file', metavar='FILE',
                        help='redirect stderr (instead of /dev/null; for debugging purposes)')
    parser.add_argument('-s', '--style', metavar='FILE',
                        help='alternative style file for TUI')
    arguments = parser.parse_args(args)
    error_msg = process_args(arguments)
    if error_msg:
        parser.error(error_msg)

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
    fuzz_process = Process(target=controller.run, args=(), kwargs={'max_cycles': arguments.max_cycles})

    try:
        fuzz_process.start()
        tui.loop.run()
    except KeyboardInterrupt:
        # No need to handle CTRL+C as SIGINT is sent by the terminal to all
        # (sub)processes.
        pass
    except Exception as e:
        # Handle every kind of TUI exceptions except for KeyboardInterrupt.
        # SIGINT will trigger a KeyboardInterrupt exception in controller,
        # thus allowing it to perform proper cleanup.
        os.kill(fuzz_process.pid, signal.SIGINT)
        logger.error('Unhandled exception in TUI.', exc_info=e)
    else:
        # Handle normal exit after 'Q' or F10. SIGINT will trigger a
        # KeyboardInterrupt exception in controller, thus allowing it to
        # perform proper cleanup.
        os.kill(fuzz_process.pid, signal.SIGINT)
    finally:
        raise ExitMainLoop()
