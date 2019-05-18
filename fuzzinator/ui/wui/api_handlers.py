# Copyright (c) 2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json

from bson.json_util import default, object_hook, RELAXED_JSON_OPTIONS
from pymongo import ASCENDING, DESCENDING
from tornado.web import HTTPError, RequestHandler


class BaseAPIHandler(RequestHandler):

    def initialize(self, wui):
        self._wui = wui

    @property
    def _controller(self):
        return self._wui.controller

    @property
    def _db(self):
        return self._wui.controller.db

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

        return dumps(_convert(obj))

    @staticmethod
    def _loads(loads, s):
        return loads(s, object_hook=object_hook)

    dumps = {
        'application/json': lambda obj: BaseAPIHandler._dumps(json.dumps, obj),
    }

    loads = {
        'application/json': lambda s: BaseAPIHandler._loads(json.loads, s),
    }

    def get_pagination_query(self, columns):
        search = self.get_query_argument('search', None)
        sort = self.get_query_argument('sort', None)
        order = self.get_query_argument('order', None)
        offset = self.get_query_argument('offset', None)
        limit = self.get_query_argument('limit', None)
        detailed = self.get_query_argument('detailed', None)

        return dict(
            filter={'$or': [{c: {'$regex': search, '$options': 'i'}} for c in columns]} if search else None,
            skip=int(offset) if offset else 0,
            limit=int(limit) if limit else 10,  # unconditional to ensure that the query is always limited
            sort={sort: {'asc': ASCENDING, 'desc': DESCENDING}[order]} if sort and order else None,
            detailed=detailed in ('true', 'True', '1') if detailed else True,
        )

    def get_content(self):
        def _mime():
            mime = self.request.headers.get('Content-Type')
            if mime in self.loads:
                return mime

            return 'application/json'

        try:
            return self.loads[_mime()](self.request.body.decode('utf-8', errors='ignore'))
        except ValueError:
            raise HTTPError(400, reason='malformed request body')   # 400 Client Error: Bad Request

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
        self.send_content(self._db.get_issues(**query),
                          total=len(self._db.get_issues(query['filter'])))


class IssueAPIHandler(BaseAPIHandler):

    def get(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid, detailed=True)
        if issue is None:
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        self.send_content(issue)

    def delete(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        self._db.remove_issue_by_oid(issue_oid)
        self._wui.send_notification('refresh_issues')
        self.set_status(204, reason='issue deleted')    # 204 Success: No Content


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
        self.send_content(list(self._db.get_stats(**query).values()),
                          total=len(self._db.get_stats(query['filter'])))


class NotFoundAPIHandler(RequestHandler):

    def prepare(self):
        raise HTTPError(404, reason='api not found')    # 404 Client Error: Not Found
