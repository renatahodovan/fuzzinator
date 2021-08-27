# Copyright (c) 2019 Tamas Keri.
# Copyright (c) 2019-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import traceback

from os.path import exists, join

from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from markdown import markdown
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler

from ...config import config_get_object
from ...formatter import JsonFormatter
from ...pkgdata import __version__
from ...tracker import TrackerError

logger = logging.getLogger(__name__)


class NotificationsHandler(WebSocketHandler):

    def initialize(self, wui):
        self._wui = wui

    # Invoked when a new WebSocket is opened.
    def open(self):
        self._wui.register_ws(self)

    # Invoked when the WebSocket is closed.
    def on_close(self):
        self._wui.unregister_ws(self)

    # Sends the given message to the client of this WebSocket.
    def send_notification(self, action, data):
        try:
            self.write_message(dumps({'action': action, 'data': data}, json_options=RELAXED_JSON_OPTIONS))
        except Exception as e:
            logger.error('Exception in send_message: %s %s', action, data, exc_info=e)
            self.on_close()
            self.close()


class BaseUIHandler(RequestHandler):

    def initialize(self, wui):
        self._wui = wui

    @property
    def _db(self):
        return self._wui.controller.db

    @property
    def _config(self):
        return self._wui.controller.config

    def render(self, *args, **kwargs):
        super().render(*args, version=__version__, **kwargs)

    def write_error(self, status_code, **kwargs):
        if 'exc_info' in kwargs:
            icon = 'sentiment_very_dissatisfied'
            if self.application.settings.get('serve_traceback'):
                exc_info = markdown('```\n%s\n```' % ''.join(traceback.format_exception(*kwargs['exc_info'])), extensions=['extra', 'fenced_code', 'codehilite'])
            else:
                exc_info = ''
        else:
            icon = 'mood_bad'
            exc_info = ''
        self.render('error.html', code=status_code, icon=icon, exc_info=exc_info)


class IssuesUIHandler(BaseUIHandler):

    def get(self):
        self.render('issues.html')


class IssueUIHandler(BaseUIHandler):

    def get(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            self.send_error(404)
            return

        formatter = config_get_object(self._config, 'sut.' + issue['sut'], ['wui_formatter', 'formatter']) or JsonFormatter()
        exporter = config_get_object(self._config, 'sut.' + issue['sut'], 'exporter')

        self.render('issue.html',
                    issue=issue,
                    issue_body=formatter(issue=issue),
                    has_tracker=self._config.has_option('sut.' + issue['sut'], 'tracker'),
                    has_exporter=exporter is not None,
                    exporter_ext=getattr(exporter, 'extension', ''))


class IssueReportUIHandler(BaseUIHandler):

    def get(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            self.send_error(404)
            return

        tracker = config_get_object(self._config, 'sut.' + issue['sut'], 'tracker')
        if not tracker:
            self.send_error(404)
            return

        formatter = config_get_object(self._config, 'sut.' + issue['sut'], ['formatter']) or JsonFormatter()

        duplicates = []
        try:
            duplicates = tracker.find_issue(issue['id'])
        except TrackerError as e:
            logger.error(str(e), exc_info=e)

        tracker_name = tracker.__class__.__name__.replace('Tracker', '')
        template = 'report-' + tracker_name.lower() + '.html'
        template = template if exists(join(self.get_template_path(), template)) else 'report.html'

        self.render(template,
                    issue_oid=issue_oid,
                    tracker_name=tracker_name,
                    title=formatter(issue=issue, format='short'),
                    body=formatter(issue=issue),
                    duplicates=duplicates,
                    settings=tracker.settings())


class ConfigUIHandler(BaseUIHandler):

    def get(self, subconfig, issue_oid=None):
        config = self._db.find_config_by_id(subconfig)
        if not config:
            self.send_error(404)
            return

        if not issue_oid:
            data = self._db.get_stats(filter={'subconfigs.subconfig': subconfig})[0]
        else:
            data = self._db.find_issue_by_oid(issue_oid)

        if not data:
            self.send_error(404)
            return

        config_src = markdown('```ini\n%s\n```' % config['src'], extensions=['extra', 'fenced_code', 'codehilite'])
        self.render('config.html', subconfig=subconfig, issue_oid=issue_oid, data=data, config_src=config_src)


class StatsUIHandler(BaseUIHandler):

    def get(self):
        self.render('stats.html')


class NotFoundHandler(BaseUIHandler):

    def prepare(self):
        self.send_error(404)
