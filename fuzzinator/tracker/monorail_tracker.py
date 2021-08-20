# Copyright (c) 2017-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import httplib2

from googleapiclient import discovery
from oauth2client.client import GoogleCredentials

from ..config import as_list
from .tracker import Tracker, TrackerError


# https://chromium.googlesource.com/infra/infra/+/master/appengine/monorail/doc/api.md
class MonorailTracker(Tracker):
    """
    Monorail_ issue tracker.

    .. _Monorail: https://opensource.google/projects/monorail

    **Mandatory parameters of the issue tracker:**

      - ``project_id``: ID (name) of the project.
      - ``issue_labels``: a list of labels (strings) to use when reporting an
        issue.
      - ``issue_status``: the status to use when reporting an issue.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            tracker=fuzzinator.tracker.MonorailTracker

            [sut.foo.tracker]
            project_id=foomium
            issue_labels=["Pri-3", "Type-Bug"]
            issue_status=Untriaged
    """

    discovery_url = 'https://monorail-prod.appspot.com/_ah/api/discovery/v1/apis/{api}/{apiVersion}/rest'
    weburl_template = 'https://bugs.chromium.org/p/{project_id}/issues/detail?id={issue_id}'

    def __init__(self, *, project_id, issue_labels, issue_status):
        self.project_id = project_id
        self.labels = as_list(issue_labels)
        self.status = issue_status

        credentials = GoogleCredentials.get_application_default()
        credentials = credentials.create_scoped(['https://www.googleapis.com/auth/userinfo.email'])
        credentials.authorize(httplib2.Http())

        self.monorail = discovery.build('monorail',
                                        'v1',
                                        discoveryServiceUrl=(self.discovery_url),
                                        credentials=credentials,
                                        cache_discovery=False)

    def find_duplicates(self, *, title):
        try:
            issues = self.monorail.issues().list(projectId=self.project_id, can='open', q=title).execute().get('items', [])
            return [(self.weburl_template.format(project_id=self.project_id, issue_id=issue['id']), issue['summary']) for issue in issues]
        except Exception as e:
            raise TrackerError('Finding possible duplicates failed') from e

    def report_issue(self, *, title, body):
        try:
            new_issue = self.monorail.issues().insert(projectId=self.project_id,
                                                      body=dict(summary=title,
                                                                labels=self.labels,
                                                                status=self.status,
                                                                projectId=self.project_id,
                                                                description=body)).execute()
            return self.weburl_template.format(project_id=self.project_id, issue_id=new_issue['id'])
        except Exception as e:
            raise TrackerError('Issue reporting failed') from e
