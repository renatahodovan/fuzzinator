# Copyright (c) 2017-2019 Renata Hodovan, Akos Kiss.
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
class MonorailTracker(BaseTracker):

    discovery_url = 'https://monorail-prod.appspot.com/_ah/api/discovery/v1/apis/{api}/{apiVersion}/rest'
    weburl_template = 'https://bugs.chromium.org/p/{project_id}/issues/detail?id={ident}'

    def __init__(self, project_id):
        self.project_id = project_id
        credentials = GoogleCredentials.get_application_default()
        credentials = credentials.create_scoped(['https://www.googleapis.com/auth/userinfo.email'])

        http = credentials.authorize(httplib2.Http())
        self.monorail = discovery.build('monorail',
                                        discoveryServiceUrl=(self.discovery_url),
                                        http=http,
                                        version='v1')

    def find_issue(self, query):
        issues = self.monorail.issues().list(projectId=self.project_id, can='open', q=query).execute().get('items', [])
        return [{'id': issue['id'],
                 'title': issue['summary'],
                 'url': self.weburl_template.format(project_id=self.project_id, ident=issue['id'])} for issue in issues]

    def report_issue(self, title, body):
        new_issue = self.monorail.issues().insert(projectId=self.project_id,
                                                  body=dict(summary=title,
                                                            description=body)).execute()
        return {'id': new_issue['id'],
                'title': new_issue['summary'],
                'url': self.weburl_template.format(project_id=self.project_id, ident=new_issue['id'])}

    def __call__(self, issue):
        pass
