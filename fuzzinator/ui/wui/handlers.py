# Copyright (c) 2019 Tamas Keri.
# Copyright (c) 2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import logging
import traceback

from bson.json_util import dumps, RELAXED_JSON_OPTIONS
from markdown import markdown
from pymongo import ASCENDING, DESCENDING
from tornado import web, websocket

from ...config import config_get_callable
from ...formatter import JsonFormatter

logger = logging.getLogger(__name__)


class SocketHandler(websocket.WebSocketHandler):

    def __init__(self, *args, wui, **kwargs):
        super().__init__(*args, **kwargs)
        self._wui = wui

    # Invoked when a new WebSocket is opened.
    def open(self):
        self._wui.register_ws(self)

    # Invoked when the WebSocket is closed.
    def on_close(self):
        self._wui.unregister_ws(self)

    # Handle incoming messages from WebSockets.
    def on_message(self, message):
        request = json.loads(message)
        action = request['action']

        handler = {
            'get_stats': self.on_get_stats,
            'get_issues': self.on_get_issues,
            'get_jobs': self.on_get_jobs,
            'cancel_job': self.on_cancel_job,
            'delete_issue': self.on_delete_issue,
            'reduce_issue': self.on_reduce_issue,
            'validate_issue': self.on_validate_issue,
        }.get(action)

        if handler:
            handler(request)
        else:
            self._wui.warning(ident='wui', msg='ERROR: Invalid {action} {message} message!'.format(action=action, message=message))

    @staticmethod
    def _build_query(request, columns, sort_pairs=True):
        data = request['data']
        search, offset, limit, sort, order = data.get('search'), data.get('offset'), data.get('limit'), data.get('sort'), data.get('order')

        query = dict(
            filter={'$or': [{c: {'$regex': search, '$options': 'i'}} for c in columns]} if search else None,
            skip=int(offset) if offset else 0,
            limit=int(limit) if limit else 10,  # unconditional to ensure that the query is always limited
            sort=[(sort, {'asc': ASCENDING, 'desc': DESCENDING}[order])] if sort and order else None,
        )
        if query['sort'] and not sort_pairs:
            query['sort'] = dict(query['sort'])
        return query

    def on_get_stats(self, request):
        query = self._build_query(request, ['fuzzer', 'sut'], sort_pairs=False)

        self.send_message('get_stats', {
            'total': len(self._wui.controller.db.get_stats(query['filter'])),
            'rows': self._wui.controller.db.get_stats(**query).values(),
        })

    def on_get_issues(self, request):
        query = self._build_query(request, ['fuzzer', 'sut', 'id'])

        self.send_message('get_issues', {
            'total': len(self._wui.controller.db.get_issues(query['filter'])),
            'rows': self._wui.controller.db.get_issues(**query),
        })

    def on_get_jobs(self, request):
        for job in dict(self._wui.jobs).values():
            self.send_message('new_job', job)

    def on_cancel_job(self, request):
        self._wui.controller.cancel_job(ident=int(request['ident']))

    def on_delete_issue(self, request):
        self._wui.controller.db.remove_issue_by_id(request['_id'])
        self.send_message('refresh_issues', None)

    def on_reduce_issue(self, request):
        issue = self._wui.controller.db.find_issue_by_id(request['_id'])
        if not self._wui.controller.add_reduce_job(issue):
            self._wui.warning(ident='wui', msg='Reduce is not possible. SUT ({sut}) has no reducer.'.format(sut='sut.' + issue['sut']))

    def on_validate_issue(self, request):
        issue = self._wui.controller.db.find_issue_by_id(request['_id'])
        if not self._wui.controller.add_validate_job(issue=issue):
            self._wui.warning(ident='wui', msg='Validate is not possible. Config has no section {sut}.'.format(sut='sut.' + issue['sut']))

    # Sends the given message to the client of this WebSocket.
    def send_message(self, action, data):
        try:
            self.write_message(dumps({'action': action, 'data': data}, json_options=RELAXED_JSON_OPTIONS))
        except Exception as e:
            logger.error('Exception in send_message: %s %s', action, data, exc_info=e)
            self.on_close()


class BaseHandler(web.RequestHandler):

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
        self.render('error.html', active_page='error', code=status_code, icon=icon, exc_info=exc_info)


class IssuesHandler(BaseHandler):

    def get(self):
        self.render('issues.html', active_page='issues')


class IssueHandler(BaseHandler):

    def __init__(self, *args, db, config, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db
        self.config = config

    def get(self, issue_id):
        issue = self.db.find_issue_by_id(issue_id)
        if issue is None:
            self.send_error(404)
            return
        formatter = config_get_callable(self.config, 'sut.' + issue['sut'], ['wui_formatter', 'formatter'])[0] or JsonFormatter
        self.render('issue.html', active_page='issue', issue=issue, issue_body=formatter(issue=issue))


class ConfigHandler(BaseHandler):

    def __init__(self, *args, db, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = db

    def get(self, subconfig, issue_id=None):
        config = self.db.find_config_by_id(subconfig)
        if not config:
            self.send_error(404)
            return

        if not issue_id:
            data = list(self.db.get_stats(filter={'configs.subconfig': subconfig}).values())[0]
        else:
            data = self.db.find_issue_by_id(issue_id)

        if not data:
            self.send_error(404)
            return

        config_src = markdown('```ini\n%s\n```' % config['src'], extensions=['extra', 'fenced_code', 'codehilite'])
        self.render('config.html', active_page='config', subconfig=subconfig, issue_id=issue_id, data=data, config_src=config_src)


class StatsHandler(BaseHandler):

    def get(self):
        self.render('stats.html', active_page='stats')


class NotFoundHandler(BaseHandler):

    def prepare(self):
        self.send_error(404)
