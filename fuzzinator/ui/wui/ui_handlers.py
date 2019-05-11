# Copyright (c) 2019 Tamas Keri.
# Copyright (c) 2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import traceback

from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from markdown import markdown
from tornado.web import RequestHandler
from tornado.websocket import WebSocketHandler

from ...config import config_get_callable
from ...formatter import JsonFormatter

logger = logging.getLogger(__name__)


class NotificationsHandler(WebSocketHandler):

    def __init__(self, *args, wui, **kwargs):
        super().__init__(*args, **kwargs)
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

    def get(self, issue_id):
        issue = self._db.find_issue_by_id(issue_id)
        if issue is None:
            self.send_error(404)
            return
        formatter = config_get_callable(self._config, 'sut.' + issue['sut'], ['wui_formatter', 'formatter'])[0] or JsonFormatter
        self.render('issue.html', issue=issue, issue_body=formatter(issue=issue))


class ConfigUIHandler(BaseUIHandler):

    def get(self, subconfig, issue_id=None):
        config = self._db.find_config_by_id(subconfig)
        if not config:
            self.send_error(404)
            return

        if not issue_id:
            data = list(self._db.get_stats(filter={'configs.subconfig': subconfig}).values())[0]
        else:
            data = self._db.find_issue_by_id(issue_id)

        if not data:
            self.send_error(404)
            return

        config_src = markdown('```ini\n%s\n```' % config['src'], extensions=['extra', 'fenced_code', 'codehilite'])
        self.render('config.html', subconfig=subconfig, issue_id=issue_id, data=data, config_src=config_src)


class StatsUIHandler(BaseUIHandler):

    def get(self):
        self.render('stats.html')


class NotFoundHandler(BaseUIHandler):

    def prepare(self):
        self.send_error(404)
