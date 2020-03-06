# Copyright (c) 2019-2020 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json

import xson

from bson.json_util import default, object_hook, RELAXED_JSON_OPTIONS
from pymongo import ASCENDING, DESCENDING
from tornado.web import HTTPError, RequestHandler

from ...config import config_get_callable


class BaseAPIHandler(RequestHandler):

    def __init__(self, *args, wui, **kwargs):
        super().__init__(*args, **kwargs)
        self._wui = wui

    @property
    def _controller(self):
        return self._wui.controller

    @property
    def _db(self):
        return self._wui.controller.db

    @property
    def _config(self):
        return self._wui.controller.config

    @staticmethod
    def _dumps(dumps, obj):
        def _convert(obj):
            if isinstance(obj, dict):
                return {k: _convert(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [_convert(v) for v in obj]
            try:
                return default(obj, json_options=RELAXED_JSON_OPTIONS)
            except TypeError:
                return obj

        return dumps(_convert(obj), indent='\t', sort_keys=True)

    @staticmethod
    def _loads(loads, s):
        return loads(s, object_hook=object_hook)

    dumps = {
        'application/json': lambda obj: BaseAPIHandler._dumps(json.dumps, obj),
        'application/xml': lambda obj: BaseAPIHandler._dumps(xson.dumps, obj),
        'text/xml': lambda obj: BaseAPIHandler._dumps(xson.dumps, obj),
    }

    loads = {
        'application/json': lambda s: BaseAPIHandler._loads(json.loads, s),
        'application/xml': lambda s: BaseAPIHandler._loads(xson.loads, s),
        'text/xml': lambda s: BaseAPIHandler._loads(xson.loads, s),
    }

    def get_pagination_query(self, columns):
        search = self.get_query_argument('search', None)
        sort = self.get_query_argument('sort', None)
        order = self.get_query_argument('order', None)
        offset = self.get_query_argument('offset', None)
        limit = self.get_query_argument('limit', None)
        detailed = self.get_query_argument('detailed', None)
        show_all = self.get_query_argument('showAll', None) in ('true', 'True', '1')

        return dict(
            filter={'$or': [{c: {'$regex': search, '$options': 'i'}} for c in columns]} if search else None,
            skip=int(offset) if offset else 0,
            limit=int(limit) if limit else None,
            sort={sort: {'asc': ASCENDING, 'desc': DESCENDING}[order]} if sort and order else None,
            detailed=detailed in ('true', 'True', '1') if detailed else True,
            session_start=None if show_all else self._controller.session_start,
        )

    def load_mime(self, mime):
        if mime in self.loads:
            return mime

        return 'application/json'

    def get_content(self):
        try:
            return self.loads[self.load_mime(self.request.headers.get('Content-Type').split(';')[0])](self.request.body.decode('utf-8', errors='ignore'))
        except ValueError:
            raise HTTPError(400, reason='malformed request body')   # 400 Client Error: Bad Request

    def get_multipart_content(self):
        if self.request.headers.get('Content-Type').split(';')[0] == 'multipart/form-data':
            try:
                return [self.loads[self.load_mime(file.content_type)](file.body.decode('utf-8', errors='ignore')) for file in self.request.files['files']]
            except ValueError:
                raise HTTPError(400, reason='malformed request body')   # 400 Client Error: Bad Request
        else:
            return [self.get_content()]

    def send_content(self, content, total=None):
        def _mime():
            format = self.get_query_argument('format', None)
            if format:
                mime = 'application/%s' % format
                if mime in self.dumps:
                    return mime

            for mime in self.request.headers.get_list('Accept'):
                if mime in self.dumps:
                    return mime

            return 'application/json'

        mime = _mime()
        self.set_header('Content-Type', mime)
        if total is not None:
            self.set_header('X-Total', total)
        self.finish(self.dumps[mime](content))


class IssuesAPIHandler(BaseAPIHandler):

    def get(self):
        query = self.get_pagination_query(['fuzzer', 'sut', 'id'])
        query['include_invalid'] = self.get_query_argument('includeInvalid', None) in ('true', 'True', '1')
        self.send_content(self._db.get_issues(**query),
                          total=len(self._db.get_issues(query['filter'], session_start=query['session_start'], include_invalid=query['include_invalid'])))

    def post(self):
        files = self.get_multipart_content()
        if not files:
            raise HTTPError(400, reason='no issue added')  # 400 Client Error: Bad Request

        issues_added = 0
        for issues in files:
            if not isinstance(issues, list):
                issues = [issues]

            for issue in issues:
                if self._db.add_issue(issue):
                    issues_added += 1

        self._wui.send_notification('refresh_issues')
        self.set_status(201, reason='issue added' if issues_added == 1 else 'issues added')   # 201 Success: Created


class IssueAPIHandler(BaseAPIHandler):

    def get(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid, detailed=True)
        if issue is None:
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        self.send_content(issue)

    def post(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        self._db.update_issue_by_oid(issue_oid, self.get_content())
        self._wui.send_notification('refresh_issues')
        self.set_status(204, reason='issue updated')  # 204 Success: No Content

    def delete(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        self._db.remove_issue_by_oid(issue_oid)
        self._wui.send_notification('refresh_issues')
        self.set_status(204, reason='issue deleted')    # 204 Success: No Content


class IssueReportAPIHandler(BaseAPIHandler):

    def post(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        tracker = config_get_callable(self._config, 'sut.' + issue['sut'], 'tracker')[0]
        if not tracker:
            raise HTTPError(404, reason='tracker not found')  # 404 Client Error: Not Found

        self._db.update_issue_by_oid(issue_oid, {'reported': tracker.report_issue(**self.get_content())['url']})
        self._wui.send_notification('refresh_issues')
        self.set_status(204, reason='issue reported')  # 204 Success: No Content


class JobsAPIHandler(BaseAPIHandler):

    def get(self):
        jobs = list(self._wui.jobs.values())
        self.send_content(jobs, total=len(jobs))

    def post(self):
        job_args = self.get_content()
        job_type = job_args.get('type')
        issue_oid = job_args.get('issue_oid')

        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        success = {
            'reduce': self._controller.add_reduce_job,
            'validate': self._controller.add_validate_job,
        }[job_type](issue)

        if not success:
            raise HTTPError(400, reason='missing config')   # 400 Client Error: Bad Request
        self.set_status(201, reason='job added')    # 201 Success: Created


class JobAPIHandler(BaseAPIHandler):

    def get(self, job_id):
        job_id = int(job_id)
        job = self._wui.jobs.get(job_id)
        if job is None:
            raise HTTPError(404, reason='job not found')    # 404 Client Error: Not Found

        self.send_content(job)

    def delete(self, job_id):
        job_id = int(job_id)
        job = self._wui.jobs.get(job_id)
        if job is None:
            raise HTTPError(404, reason='job not found')    # 404 Client Error: Not Found

        self._controller.cancel_job(job_id)
        self.set_status(204, reason='job cancelled')    # 204 Success: No Content


class StatsAPIHandler(BaseAPIHandler):

    def get(self):
        query = self.get_pagination_query(['fuzzer', 'sut'])
        query['session_baseline'] = self._controller.session_baseline if query['session_start'] else None
        self.send_content(self._db.get_stats(**query),
                          total=len(self._db.get_stats(query['filter'], session_start=query['session_start'], session_baseline=query['session_baseline'])))


class NotFoundAPIHandler(RequestHandler):

    def prepare(self):
        raise HTTPError(404, reason='api not found')    # 404 Client Error: Not Found
