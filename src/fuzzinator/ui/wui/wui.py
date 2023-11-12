# Copyright (c) 2019 Tamas Keri.
# Copyright (c) 2019-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os
import signal
import ssl
import sys

from multiprocessing import Lock, Manager, Process, Queue
from queue import Empty

from rainbow_logging_handler import RainbowLoggingHandler
from tornado import ioloop, web

from ... import Controller
from .api_handlers import IssueAPIHandler, IssueReportAPIHandler, IssuesAPIHandler, JobAPIHandler, JobsAPIHandler, NotFoundAPIHandler, StatsAPIHandler
from .ui_handlers import ConfigUIHandler, IssueReportUIHandler, IssuesUIHandler, IssueUIHandler, NotFoundHandler, NotificationsHandler, ResourceLoader, StaticResourceHandler, StatsUIHandler
from .wui_listener import WuiListener

logger = logging.getLogger(__name__)
root_logger = logging.getLogger()


class Wui:

    def __init__(self, controller, port, address, cert, key, debug):
        self.events = Queue()
        self.lock = Lock()
        # Main controller of Fuzzinator.
        self.controller = controller
        self.controller.listener += WuiListener(self.events, self.lock)
        # Collection of request handlers that make up a web application.
        handler_args = {'wui': self}
        self.app = web.Application([(r'/', IssuesUIHandler, handler_args),
                                    (r'/issues/([0-9a-f]{24})', IssueUIHandler, handler_args),
                                    (r'/issues/([0-9a-f]{24})/report', IssueReportUIHandler, handler_args),
                                    (r'/stats', StatsUIHandler, handler_args),
                                    (r'/configs/([0-9a-f]{9})(?:/([0-9a-f]{24}))?', ConfigUIHandler, handler_args),
                                    (r'/notifications', NotificationsHandler, handler_args),
                                    (r'/api/issues', IssuesAPIHandler, handler_args),
                                    (r'/api/issues/([0-9a-f]{24})', IssueAPIHandler, handler_args),
                                    (r'/api/issues/([0-9a-f]{24})/report', IssueReportAPIHandler, handler_args),
                                    (r'/api/jobs', JobsAPIHandler, handler_args),
                                    (r'/api/jobs/([0-9]+)', JobAPIHandler, handler_args),
                                    (r'/api/stats', StatsAPIHandler, handler_args),
                                    (r'/api/.*', NotFoundAPIHandler)],
                                   default_handler_class=NotFoundHandler, default_handler_args=handler_args,
                                   template_loader=ResourceLoader(__package__, 'resources/templates'),
                                   static_handler_class=StaticResourceHandler, static_handler_args={'package': __package__}, static_path='resources/static',
                                   autoreload=False, debug=debug)
        # Starts an HTTP server for this application on the given port.
        if cert:
            ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ssl_ctx.check_hostname = False
            ssl_ctx.verify_mode = ssl.CERT_NONE
            ssl_ctx.load_cert_chain(certfile=cert, keyfile=key)
        else:
            ssl_ctx = None
        self.server = self.app.listen(port, address, ssl_options=ssl_ctx)
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
            except Empty:
                break
            except Exception as e:
                logger.warning('Exception in WUI', exc_info=e)
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

    def on_job_added(self, type, **kwargs):
        job = kwargs
        job.update(type=type, status='inactive')
        self.jobs[job['job_id']] = job
        self.send_notification('job_added', job)

    def on_fuzz_job_added(self, **kwargs):
        self.on_job_added('fuzz', **kwargs)

    def on_reduce_job_added(self, **kwargs):
        self.on_job_added('reduce', **kwargs)

    def on_update_job_added(self, **kwargs):
        self.on_job_added('update', **kwargs)

    def on_validate_job_added(self, **kwargs):
        self.on_job_added('validate', **kwargs)

    def on_job_removed(self, **kwargs):
        del self.jobs[kwargs['job_id']]
        self.send_notification('job_removed', kwargs)

    def on_job_activated(self, **kwargs):
        job = self.jobs[kwargs['job_id']]
        job.update(status='active')
        self.jobs[kwargs['job_id']] = job
        self.send_notification('job_activated', kwargs)

    def on_job_progressed(self, **kwargs):
        job = self.jobs[kwargs['job_id']]
        job.update(progress=kwargs['progress'])
        self.jobs[kwargs['job_id']] = job
        self.send_notification('job_progressed', kwargs)

    def on_issue_added(self, **kwargs):
        self.send_notification('issue_added')
        self.send_notification('refresh_issues')

    def on_issue_updated(self, **kwargs):
        self.send_notification('refresh_issues')

    def on_issue_invalidated(self, **kwargs):
        self.send_notification('refresh_issues')

    def on_issue_reduced(self, **kwargs):
        self.send_notification('refresh_issues')

    def on_stats_updated(self, **kwargs):
        self.send_notification('refresh_stats')

    def warning(self, job_id, msg):
        logger.warning(msg)


def execute(arguments):
    if not root_logger.hasHandlers():
        root_logger.addHandler(RainbowLoggingHandler(sys.stdout))
    # The INFO level of Tornado's access logging is too chatty, hence they are
    # not displayed on INFO level.
    if root_logger.getEffectiveLevel() == logging.INFO:
        logging.getLogger('tornado.access').setLevel(logging.WARNING)
    logger.info('Server started at: %s://%s:%d', 'https' if arguments.cert else 'http', arguments.bind_ip or 'localhost', arguments.port)

    controller = Controller(config=arguments.config)
    wui = Wui(controller, arguments.port, arguments.bind_ip, arguments.cert, arguments.key, arguments.develop)
    fuzz_process = Process(target=controller.run, args=(), kwargs={'max_cycles': arguments.max_cycles, 'validate': arguments.validate, 'reduce': arguments.reduce})

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
