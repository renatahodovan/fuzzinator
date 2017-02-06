# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
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

from string import Template

from .base import BaseTracker


class GithubReport(BaseTracker):

    def __init__(self, repository, template, title=None):
        BaseTracker.__init__(self, template=title, title=title)
        self.repository = repository
        self.template = template
        self.ghapi = Github().get_repo(self.repository)

    @property
    def logged_in(self):
        try:
            gh.get_user().id
            return True
        except:
            return False

    def login(self, username, pwd):
        try:
            gh = Github(username, pwd)
            # This expression has no effect but will throw an exception if the authentication failed.
            gh.get_user().id
            self.ghapi = gh.get_repo(self.repository)
            return True
        except BadCredentialsException:
            return False

    def format_issue(self, issue):
        with open(self.template, 'r') as f:
            return Template(f.read()).substitute(self.decode_issue(issue))

    def find_issue(self, issue):
        options = []
        pages = self.ghapi.get_issues(state='open')
        idx = 0
        while True:
            page = pages.get_page(idx)
            idx += 1
            if not page:
                break
            for entry in page:
                ident = issue['id'].decode('utf-8', errors='ignore') if isinstance(issue['id'], bytes) else issue['id']
                if all(word in entry.body for word in ident.split()):
                    options.append(entry)
        return options

    def report_issue(self, report_details):
        return self.ghapi.create_issue(title=report_details['title'],
                                       body=report_details['body'])

    def __call__(self, issue):
        pass
