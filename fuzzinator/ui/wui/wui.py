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

from .handlers import ConfigHandler, IndexHandler, IssueHandler, NotFoundHandler, SocketHandler, StatsHandler
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
        self.app = web.Application([(r'/', IndexHandler),
                                    (r'/issue/([0-9a-f]{24})', IssueHandler, dict(db=controller.db, config=controller.config)),
                                    (r'/stats', StatsHandler),
                                    (r'/config/([0-9a-f]{9})/([0-9a-z]+)', ConfigHandler, dict(db=controller.db)),
                                    (r'/wui', SocketHandler, dict(wui=self))],
                                   default_handler_class=NotFoundHandler,
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

    def send_message(self, action, data):
        for socket in self.sockets:
            socket.send_message(action, data)

    def new_fuzz_job(self, **kwargs):
        self.jobs[kwargs['ident']] = dict(kwargs, status='inactive', type='fuzz')
        self.send_message('new_fuzz_job', kwargs)

    def new_reduce_job(self, **kwargs):
        self.jobs[kwargs['ident']] = dict(kwargs, status='inactive', type='reduce')
        self.send_message('new_reduce_job', kwargs)

    def new_update_job(self, **kwargs):
        self.jobs[kwargs['ident']] = dict(kwargs, status='inactive', type='update')
        self.send_message('new_update_job', kwargs)

    def new_validate_job(self, **kwargs):
        self.jobs[kwargs['ident']] = dict(kwargs, status='inactive', type='validate')
        self.send_message('new_validate_job', kwargs)

    def remove_job(self, **kwargs):
        del self.jobs[kwargs['ident']]
        self.send_message('remove_job', kwargs)

    def activate_job(self, **kwargs):
        self.jobs[kwargs['ident']] = dict(self.jobs[kwargs['ident']], status='active')
        self.send_message('activate_job', kwargs)

    def job_progress(self, **kwargs):
        self.jobs[kwargs['ident']]['progress'] = kwargs['progress']
        self.send_message('job_progress', kwargs)

    def new_issue(self, ident, issue):
        self.send_message('new_issue', issue)

    def update_issue(self, ident, issue):
        self.send_message('update_issue', issue)

    def invalid_issue(self, ident, issue):
        self.send_message('invalid_issue', issue)

    def reduced_issue(self, ident, issue):
        self.send_message('reduced_issue', issue)

    def update_fuzz_stat(self, **kwargs):
        self.send_message('update_fuzz_stat', list(self.controller.db.get_stats(filter=kwargs).values()))

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
