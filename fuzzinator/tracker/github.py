# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from github import Github, BadCredentialsException
from string import Template

from .base import BaseTracker


class GithubReport(BaseTracker):

    def __init__(self, repository, template, title=None):
        BaseTracker.__init__(self, template=title, title=title)
        self.repository = repository
        self.template = template
        self.ghapi = None

    @property
    def logged_in(self):
        return self.ghapi is not None
    
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
            for issue in page:
                if all(word in issue.body for word in issue['id'].decode('utf-8', errors='ignore').split()):
                    options.append(issue)
        return options

    def report_issue(self, report_details, extension=None):
        return self.ghapi.create_issue(title=report_details['title'],
                                       body=report_details['body'])

    def __call__(self, issue):
        pass
