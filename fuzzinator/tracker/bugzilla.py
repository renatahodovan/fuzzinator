# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from bugzilla import *

from .base import BaseTracker


class BugzillaReport(BaseTracker):

    def __init__(self, product, url, template, title=None):
        BaseTracker.__init__(self, template=template, title=title)
        self.product = product
        self.bzapi = Bugzilla(url)

        # Remove old token and cookie files since they may be outdated.
        if os.path.exists(self.bzapi.tokenfile):
            os.remove(self.bzapi.tokenfile)
        if os.path.exists(self.bzapi.cookiefile):
            os.remove(self.bzapi.cookiefile)

    @property
    def logged_in(self):
        return self.bzapi.user

    def login(self, username, pwd):
        try:
            self.bzapi.login(user=username, password=pwd)
            return True
        except BugzillaError:
            return False

    def find_issue(self, issue):
        return self.bzapi.query(self.bzapi.build_query(product=self.product,
                                                       status=['NEW', 'REOPENED', 'ASSIGNED'],
                                                       short_desc=self.title(issue),
                                                       include_fields=['id', 'summary', 'weburl']))

    def report_issue(self, report_details, test, extension):
        create_info = self.bzapi.build_createbug(product=report_details['product'],
                                                 component=report_details['component'],
                                                 summary=report_details['summary'],
                                                 version=report_details['version'],
                                                 description=report_details['description'],
                                                 blocks=report_details['blocks'])

        bug = self.bzapi.createbug(create_info)
        test_file = 'test.{ext}'.format(ext=extension)
        with open(test_file, 'wb') as f:
            f.write(test)
        self.bzapi.attachfile(idlist=bug.bug_id, attachfile=test_file, description='Test', is_patch=False)
        os.remove(test_file)
        return bug

    def __call__(self, issue):
        pass

    def issue_url(self, issue):
        return issue.weburl
