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
    from github import Github, BadCredentialsException
except ImportError:
    pass

from .base import BaseTracker


class GithubTracker(BaseTracker):

    def __init__(self, repository):
        self.repository = repository
        self.ghapi = Github().get_repo(self.repository)
        self.gh = None

    @property
    def logged_in(self):
        try:
            _ = self.gh.get_user().id
            return True
        except Exception:
            return False

    def login(self, username, pwd):
        try:
            self.gh = Github(username, pwd)
            # This expression has no effect but will throw an exception if the authentication failed.
            _ = self.gh.get_user().id
            self.ghapi = self.gh.get_repo(self.repository)
            return True
        except BadCredentialsException:
            return False

    def find_issue(self, query):
        options = []
        pages = self.ghapi.get_issues(state='open')
        idx = 0
        while True:
            page = pages.get_page(idx)
            idx += 1
            if not page:
                break
            for entry in page:
                if all(word in entry.body for word in query.split()):
                    options.append(entry)
        return options

    def report_issue(self, title, body):
        return self.ghapi.create_issue(title=title, body=body)

    def __call__(self, issue):
        pass

    def issue_url(self, issue):
        return issue.html_url
