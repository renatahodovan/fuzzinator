# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

try:
    # FIXME: very nasty, but a recent PyGithub version began to depend on
    # pycrypto transitively, which is a PITA on Windows (can easily fail with an
    # ``ImportError: No module named 'winrandom'``) -- so, we just don't care
    # for now if we cannot load the github module at all. This workaround just
    # postpones the error to the point when ``GithubReport`` is actually used,
    # so be warned, don't do that on Windows!
    from github import Github
except ImportError:
    pass

from .base import BaseTracker


class GithubTracker(BaseTracker):

    def __init__(self, repository, token=None):
        self.org, self.repository = repository.split('/')
        self.ghapi = Github(login_or_token=token)
        self.project = self.ghapi.get_repo(repository)

    def find_issue(self, query):
        return list(self.ghapi.search_issues('+'.join(query.split()), state='open', org=self.org, repo=self.repository))

    def report_issue(self, title, body):
        return self.project.create_issue(title=title, body=body)

    def __call__(self, issue):
        pass

    def issue_url(self, issue):
        return issue.html_url
