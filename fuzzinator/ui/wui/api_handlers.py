# Copyright (c) 2019-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import traceback

from io import BytesIO
from zipfile import ZipFile, ZIP_DEFLATED

import xson

from bson.json_util import default, object_hook, RELAXED_JSON_OPTIONS
from pymongo import ASCENDING, DESCENDING
from tornado.web import HTTPError, RequestHandler

from ...config import config_get_object
from ...tracker import TrackerError


class BaseAPIHandler(RequestHandler):

    def initialize(self, wui):
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
        if search:
            search = search.strip()
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
        except ValueError as exc:
            self._wui.send_notification('error', data={'title': 'Content loading failed', 'body': str(exc)})
            raise HTTPError(400, reason='malformed request body') from exc  # 400 Client Error: Bad Request

    def get_multipart_content(self):
        if self.request.headers.get('Content-Type').split(';')[0] == 'multipart/form-data':
            try:
                return [self.loads[self.load_mime(file.content_type)](file.body.decode('utf-8', errors='ignore')) for file in self.request.files['files']]
            except ValueError as exc:
                self._wui.send_notification('error', data={'title': 'Multipart content loading failed', 'body': str(exc)})
                raise HTTPError(400, reason='malformed request body') from exc  # 400 Client Error: Bad Request
        else:
            return [self.get_content()]

    def send_content(self, content, total=None):
        def _mime():
            format = self.get_query_argument('format', None)
            if format:
                mime = f'application/{format}'
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

    def send_export(self, issues):
        zipbuf = BytesIO()
        with ZipFile(zipbuf, mode='w', compression=ZIP_DEFLATED) as zf:
            for issue in issues:
                exporter = config_get_object(self._config, f'sut.{issue["sut"]}', 'exporter')
                if not exporter:
                    continue  # silently skip issues with no exporter
                ext = getattr(exporter, 'extension', '')
                zf.writestr(str(issue['_id']) + ext, exporter(issue=issue))

        self.set_header('Content-Type', 'application/zip')
        self.finish(zipbuf.getvalue())

    def get(self):
        query = self.get_pagination_query(['fuzzer', 'sut', 'id'])
        query['include_invalid'] = self.get_query_argument('includeInvalid', None) in ('true', 'True', '1')
        if self.get_query_argument('format', None) == 'custom':
            self.send_export(self._db.get_issues(**query))
        else:
            self.send_content(self._db.get_issues(**query),
                              total=len(self._db.get_issues(query['filter'], session_start=query['session_start'], include_invalid=query['include_invalid'])))

    def post(self):
        files = self.get_multipart_content()
        if not files:
            self._wui.send_notification('error', data={'title': 'Issue uploading failed', 'body': 'Nothing to upload.'})
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

    def send_export(self, issue):
        exporter = config_get_object(self._config, f'sut.{issue["sut"]}', 'exporter')
        if not exporter:
            self._wui.send_notification('error', data={'title': 'Issue export failed',
                                                       'body': f'The exporter setup is missing from the configuration (sut.{issue["sut"]}.exporter).'})
            raise HTTPError(404, reason='exporter not found')  # 404 Client Error: Not Found

        if getattr(exporter, 'type', None):
            self.set_header('Content-Type', exporter.type)
        self.finish(exporter(issue=issue))

    def get(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid, detailed=True)
        if issue is None:
            self._wui.send_notification('error', data={'title': 'Issue request failed',
                                                       'body': f'No issue with id={issue_oid}.'})
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        if self.get_query_argument('format', None) == 'custom':
            self.send_export(issue)
        else:
            self.send_content(issue)

    def post(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            self._wui.send_notification('error', data={'title': 'Issue editing failed',
                                                       'body': f'No issue with id={issue_oid}.'})
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        self._db.update_issue_by_oid(issue_oid, self.get_content())
        self._wui.send_notification('refresh_issues')
        self.set_status(204, reason='issue updated')  # 204 Success: No Content

    def delete(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            self._wui.send_notification('error', data={'title': 'Issue deletion failed',
                                                       'body': f'No issue with id={issue_oid}.'})
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        self._db.remove_issue_by_oid(issue_oid)
        self._wui.send_notification('refresh_issues')
        self.set_status(204, reason='issue deleted')    # 204 Success: No Content


class IssueReportAPIHandler(BaseAPIHandler):

    def post(self, issue_oid):
        issue = self._db.find_issue_by_oid(issue_oid)
        if issue is None:
            self._wui.send_notification('error', data={'title': 'Issue reporting failed',
                                                       'body': f'No issue with id={issue_oid}.'})
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        tracker = config_get_object(self._config, f'sut.{issue["sut"]}', 'tracker')
        if not tracker:
            self._wui.send_notification('error', data={'title': 'Issue reporting failed',
                                                       'body': f'The tracker setup is missing from the configuration (sut.{issue["sut"]}.tracker).'})
            raise HTTPError(404, reason='tracker not found')  # 404 Client Error: Not Found

        try:
            self._db.update_issue_by_oid(issue_oid, {'reported': tracker.report_issue(**self.get_content())})
            self._wui.send_notification('refresh_issues')
            self.set_status(204, reason='issue reported')  # 204 Success: No Content
        except TrackerError as e:
            data = {'title': str(e), 'body': str(e.__cause__)}
            if self.application.settings.get('serve_traceback'):
                data['exc_info'] = traceback.format_exc()
            self._wui.send_notification('error', data=data)
            self.set_status(400, reason='issue report failed')  # 400 Client Error: Bad Request


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
            self._wui.send_notification('error', data={'title': f'{job_type.capitalize()} job creation failed',
                                                       'body': f'No issue with id={issue_oid}.'})
            raise HTTPError(404, reason='issue not found')  # 404 Client Error: Not Found

        success = {
            'reduce': self._controller.add_reduce_job,
            'validate': self._controller.add_validate_job,
        }[job_type](issue)

        if not success:
            self._wui.send_notification('error',
                                        data={'title': f'{job_type.capitalize()} job creation failed',
                                              'body': f'The {job_type} setup is missing from the configuration (sut.{issue["sut"]}{".reduce" if job_type == "reduce" else ""}).'})
            raise HTTPError(400, reason='missing config')   # 400 Client Error: Bad Request
        self.set_status(201, reason='job added')    # 201 Success: Created


class JobAPIHandler(BaseAPIHandler):

    def get(self, job_id):
        job_id = int(job_id)
        job = self._wui.jobs.get(job_id)
        if job is None:
            self._wui.send_notification('error', data={'title': 'Job request failed',
                                                       'body': f'No job with id={job_id}.'})
            raise HTTPError(404, reason='job not found')    # 404 Client Error: Not Found

        self.send_content(job)

    def delete(self, job_id):
        job_id = int(job_id)
        job = self._wui.jobs.get(job_id)
        if job is None:
            self._wui.send_notification('error', data={'title': 'Job cancelation failed',
                                                       'body': f'No job with id={job_id}.'})
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
