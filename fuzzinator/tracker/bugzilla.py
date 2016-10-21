# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from bugzilla import *
from string import Template

from .base import BaseTracker


class BugzillaReport(BaseTracker):

    def __init__(self, url, template, title=None):
        BaseTracker.__init__(self, template=template, title=title)
        self.template = template
        self.bzapi = Bugzilla(url)

    @property
    def logged_in(self):
        return self.bzapi.user

    def login(self, username, pwd):
        try:
            self.bzapi.login(user=username, password=pwd)
            return True
        except BugzillaError:
            return False

    def format_issue(self, issue):
        with open(self.template, 'r') as f:
            return Template(f.read()).substitute(self.decode_issue(issue))

    def find_issue(self, issue):
        return self.bzapi.query(self.bzapi.build_query(product='WebKit',
                                                       status=['NEW', 'REOPENED', 'ASSIGNED'],
                                                       short_desc=self.title(issue),
                                                       include_fields=['id', 'summary', 'weburl']))

    def report_issue(self, report_details, extension):
        create_info = self.bzapi.build_createbug(product=report_details['product'],
                                                 component=report_details['component'],
                                                 summary=report_details['summary'],
                                                 version=report_details['version'],
                                                 description=report_details['description'],
                                                 blocks=report_details['blocks'])

        bug = self.bzapi.createbug(create_info)
        test_file = 'test.{ext}'.format(ext=extension)
        with open(test_file, 'wb') as f:
            f.write(report_details['test'])
        self.bzapi.attachfile(idlist=bug.bug_id, attachfile=test_file, description='Test', is_patch=False)
        os.remove(test_file)
        return bug

    def __call__(self, issue):
        pass
