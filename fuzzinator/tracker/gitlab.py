# Copyright (c) 2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from gitlab import Gitlab

from .base import BaseTracker


class GitlabTracker(BaseTracker):

    def __init__(self, url, project, private_token=None):
        gl = Gitlab(url, private_token=private_token)
        gl.auth()
        self.project = gl.projects.get(gl.search('projects', project)[0]['id'])

    def find_issue(self, query):
        return [issue for issue in self.project.search('issues', query) if issue['state'] == 'opened']

    def report_issue(self, title, body):
        return self.project.issues.create(dict(title=title, description=body))

    def __call__(self, issue):
        pass

    def issue_url(self, issue):
        return issue.attributes['web_url']
