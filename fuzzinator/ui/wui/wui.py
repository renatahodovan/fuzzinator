# Copyright (c) 2019 Tamas Keri.
# Copyright (c) 2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import argparse
import logging
import os
import signal
import sys

from multiprocessing import Lock, Manager, Process, Queue
from pkg_resources import resource_filename
from rainbow_logging_handler import RainbowLoggingHandler
from tornado import ioloop, web

from ... import Controller
from .. import build_parser, process_args

from .api_handlers import IssueAPIHandler, IssuesAPIHandler, JobAPIHandler, JobsAPIHandler, NotFoundAPIHandler, StatsAPIHandler
from .ui_handlers import ConfigUIHandler, IssuesUIHandler, IssueUIHandler, NotFoundHandler, NotificationsHandler, StatsUIHandler
from .wui_listener import WuiListener

logger = logging.getLogger()


class Wui(object):

    def __init__(self, controller, port, address, debug):
        self.events = Queue()
        self.lock = Lock()
        # Main controller of Fuzzinator.
        self.controller = controller
        self.controller.listener += WuiListener(self.events, self.lock)
        # Collection of request handlers that make up a web application.
        handler_args = dict(wui=self)
        self.app = web.Application([(r'/', IssuesUIHandler, handler_args),
                                    (r'/issues/([0-9a-f]{24})', IssueUIHandler, handler_args),
                                    (r'/stats', StatsUIHandler, handler_args),
                                    (r'/configs/([0-9a-f]{9})(?:/([0-9a-f]{24}))?', ConfigUIHandler, handler_args),
                                    (r'/notifications', NotificationsHandler, handler_args),
                                    (r'/api/issues', IssuesAPIHandler, handler_args),
                                    (r'/api/issues/([0-9a-f]{24})', IssueAPIHandler, handler_args),
                                    (r'/api/jobs', JobsAPIHandler, handler_args),
                                    (r'/api/jobs/([0-9]+)', JobAPIHandler, handler_args),
                                    (r'/api/stats', StatsAPIHandler, handler_args),
                                    (r'/api/.*', NotFoundAPIHandler)],
                                   default_handler_class=NotFoundHandler, default_handler_args=handler_args,
                                   template_path=resource_filename(__name__, os.path.join('resources', 'templates')),
                                   static_path=resource_filename(__name__, os.path.join('resources', 'static')),
                                   autoreload=False, debug=debug)
        # Starts an HTTP server for this application on the given port.
        self.server = self.app.listen(port, address)
        # List of opened WebSockets.
        self.sockets = set()
        # Share dict between processes.
        self.jobs = Manager().dict()

    def update_ui(self):
        while True:
            try:
                event = self.events.get_nowait()
                if hasattr(self, event['fn']):
                    getattr(self, event['fn'])(**event['kwargs'])
            except Exception:
                break

    def register_ws(self, socket):
        self.sockets.add(socket)

    def unregister_ws(self, socket):
        if socket in self.sockets:
            self.sockets.remove(socket)

    def stop_ws(self):
        for socket in self.sockets:
            socket.close()

    def send_notification(self, action, data=None):
        for socket in self.sockets:
            socket.send_notification(action, data)

    def new_job(self, type, **kwargs):
        job = kwargs
        job.update(type=type, status='inactive')
        self.jobs[job['ident']] = job
        self.send_notification('new_job', job)

    def new_fuzz_job(self, **kwargs):
        self.new_job('fuzz', **kwargs)

    def new_reduce_job(self, **kwargs):
        self.new_job('reduce', **kwargs)

    def new_update_job(self, **kwargs):
        self.new_job('update', **kwargs)

    def new_validate_job(self, **kwargs):
        self.new_job('validate', **kwargs)

    def remove_job(self, **kwargs):
        del self.jobs[kwargs['ident']]
        self.send_notification('remove_job', kwargs)

    def activate_job(self, **kwargs):
        job = self.jobs[kwargs['ident']]
        job.update(status='active')
        self.jobs[kwargs['ident']] = job
        self.send_notification('activate_job', kwargs)

    def job_progress(self, **kwargs):
        job = self.jobs[kwargs['ident']]
        job.update(progress=kwargs['progress'])
        self.jobs[kwargs['ident']] = job
        self.send_notification('job_progress', kwargs)

    def new_issue(self, **kwargs):
        self.send_notification('new_issue')
        self.send_notification('refresh_issues')

    def update_issue(self, **kwargs):
        self.send_notification('refresh_issues')

    def invalid_issue(self, **kwargs):
        self.send_notification('refresh_issues')

    def reduced_issue(self, **kwargs):
        self.send_notification('refresh_issues')

    def update_fuzz_stat(self, **kwargs):
        self.send_notification('refresh_stats')

    def warning(self, ident, msg):
        logger.warning(msg)


def execute(args=None, parser=None):
    parser = build_parser(parent=parser)
    parser.add_argument('--bind-ip', metavar='NAME/IP', default='localhost',
                        help='hostname or IP address to start the service on (default: %(default)s)')
    parser.add_argument('--bind-ip-all', dest='bind_ip', action='store_const', const='', default=argparse.SUPPRESS,
                        help='bind service to all available addresses (alias for --bind-ip=%(const)r)')
    parser.add_argument('--port', metavar='NUM', default=8080, type=int,
                        help='port to start the service on (default: %(default)d)')
    parser.add_argument('--develop', action='store_true',
                        help='run the service in development mode')
    arguments = parser.parse_args(args)
    error_msg = process_args(arguments)
    if error_msg:
        parser.error(error_msg)

    logger.addHandler(RainbowLoggingHandler(sys.stdout))
    # The INFO level of Tornado's access logging is too chatty, hence they are
    # not displayed on INFO level.
    if logger.getEffectiveLevel() == logging.INFO:
        logging.getLogger('tornado.access').setLevel(logging.WARNING)
    logger.info('Server started at: http://%s:%d', arguments.bind_ip or 'localhost', arguments.port)

    controller = Controller(config=arguments.config)
    wui = Wui(controller, arguments.port, arguments.bind_ip, arguments.develop)
    fuzz_process = Process(target=controller.run, args=())

    iol = ioloop.IOLoop.instance()
    iol_clb = ioloop.PeriodicCallback(wui.update_ui, 1000)

    try:
        fuzz_process.start()
        iol_clb.start()
        iol.start()
    except KeyboardInterrupt:
        # No need to handle CTRL+C as SIGINT is sent by the terminal to all
        # (sub)processes.
        pass
    except Exception as e:
        # Handle every kind of WUI exceptions except for KeyboardInterrupt.
        # SIGINT will trigger a KeyboardInterrupt exception in controller,
        # thus allowing it to perform proper cleanup.
        os.kill(fuzz_process.pid, signal.SIGINT)
        logger.error('Unhandled exception in WUI.', exc_info=e)
    else:
        # SIGINT will trigger a KeyboardInterrupt exception in controller,
        # thus allowing it to perform proper cleanup.
        os.kill(fuzz_process.pid, signal.SIGINT)
    finally:
        wui.stop_ws()
        iol_clb.stop()
        iol.add_callback(iol.stop)
