# Copyright (c) 2019-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from gitlab import Gitlab, exceptions

from .base import BaseTracker, TrackerError


class GitlabTracker(BaseTracker):

    def __init__(self, url, project, private_token=None):
        gl = Gitlab(url, private_token=private_token)
        gl.auth()
        self.project = gl.projects.get(gl.search('projects', project)[0]['id'])

    def find_issue(self, query):
        try:
            issues = [issue for issue in self.project.search('issues', query) if issue['state'] == 'opened']
            return [{'id': issue['id'],
                     'title': issue['title'],
                     'url': issue['web_url']} for issue in issues]
        except (exceptions.GitlabAuthenticationError, exceptions.GitlabSearchError) as e:
            raise TrackerError('Finding possible duplicates failed') from e

    def report_issue(self, title, body):
        try:
            new_issue = self.project.issues.create(dict(title=title, description=body))
            return {'id': new_issue.attributes['id'],
                    'title': new_issue.attributes['title'],
                    'url': new_issue.attributes['web_url']}
        except (exceptions.GitlabAuthenticationError, exceptions.GitlabCreateError) as e:
            raise TrackerError('Issue reporting failed') from e
