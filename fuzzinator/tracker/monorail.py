# Copyright (c) 2017-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import httplib2

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from .base import BaseTracker


# https://chromium.googlesource.com/infra/infra/+/master/appengine/monorail/doc/api.md
class MonorailReport(BaseTracker):

    def __init__(self, project_id, template, title=None):
        BaseTracker.__init__(self, template=template, title=title)
        self.project_id = project_id
        self.monorail = None
        self.login()

    @property
    def logged_in(self):
        return self.monorail is not None

    def login(self, *args):
        credentials = GoogleCredentials.get_application_default()
        credentials = credentials.create_scoped(['https://www.googleapis.com/auth/userinfo.email'])

        http = credentials.authorize(httplib2.Http())
        self.monorail = discovery.build('monorail',
                                        discoveryServiceUrl=('https://monorail-prod.appspot.com/_ah/api/discovery/v1/apis/{api}/{apiVersion}/rest'),
                                        http=http,
                                        version='v1')

    def find_issue(self, issue):
        return self.monorail.issues().list(projectId=self.project_id, can='open',
                                           q=issue['id'].decode('utf-8', errors='ignore')).execute().get('items', [])

    def report_issue(self, title, body):
        return self.monorail.issues().insert(projectId=self.project_id,
                                             body=dict(summary=title,
                                                       description=body))

    def __call__(self, issue):
        pass

    def issue_url(self, issue):
        return 'https://bugs.chromium.org/p/{project_id}/issues/detail?id={ident}'.format(project_id=self.project_id,
                                                                                          ident=issue['id'])
