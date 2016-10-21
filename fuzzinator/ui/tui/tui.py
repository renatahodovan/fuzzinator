# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import configparser
import json
import os
import pkgutil
import time
import sys

from multiprocessing import Lock, Process, Queue
from os.path import join
from urwid import connect_signal, raw_display, util, ExitMainLoop, MainLoop, PopUpLauncher

from fuzzinator import Controller
from fuzzinator.ui import arg_parser
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
        try:
            with self.lock:
                event = self.events.get(timeout=3)

            if hasattr(self, event['fn']):
                getattr(self, event['fn'])(**event['kwargs'])
        except:
            pass

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

    def warning(self, msg):
        self.view._emit('warning', msg)

    @staticmethod
    def exit_handler(key):
        if key in ('q', 'Q', 'f10'):
            raise ExitMainLoop()


def execute(args=None, parser=None):
    parser = arg_parser.build_parser(parent=parser)
    parser.add_argument('--force-encoding', default=None, choices=['utf-8', 'ascii'], help='force text encoding used for TUI widgets (instead of autodetect)')
    # TODO: reset default to False before release
    parser.add_argument('--log-file', metavar='FILE', help='redirect stderr (instead of /dev/null; for debugging purposes)')
    parser.add_argument('-s', '--style', metavar='FILE', help='alternative style file for TUI')
    arguments = parser.parse_args(args)

    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(arguments.config)

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
    style = [(key, *entry[key]) for entry in raw_style for key in entry]

    if arguments.force_encoding:
        util.set_encoding(arguments.force_encoding)

    controller = Controller(config=config)
    tui = Tui(controller, style=style)
    controller.listener = TuiListener(tui.pipe, tui.events, tui.lock)
    fuzz_process = Process(target=controller.run, args=())

    try:
        fuzz_process.start()
        tui.loop.run()
    finally:
        controller.kill_child_processes()
        fuzz_process.terminate()
        raise ExitMainLoop()
