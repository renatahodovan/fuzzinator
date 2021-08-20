# Copyright (c) 2016-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from io import BytesIO

from bugzilla import *

from .tracker import Tracker, TrackerError


class BugzillaTracker(Tracker):
    """
    Bugzilla_ issue tracker.

    .. _Bugzilla: https://www.bugzilla.org/

    **Mandatory parameters of the issue tracker:**

      - ``url``: URL of the Bugzilla installation.
      - ``product``: the name of the SUT in the Bugzilla.

    **Optional parameter of the issue tracker:**

      - ``api_key``: an API key for authenticating.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            tracker=fuzzinator.tracker.BugzillaTracker

            [sut.foo.tracker]
            url=https://bugzilla.example.org
            product=foo
            api_key=1234567890123456789012345678901234567890
    """

    ui_extension = {
        'tui': 'fuzzinator.ui.tui.BugzillaReportDialog',
        'wui': 'report/bugzilla.html',
    }

    def __init__(self, *, product, url, api_key=None):
        self.product = product
        self.bzapi = Bugzilla(url, api_key=api_key)

        # Remove old token and cookie files since they may be outdated.
        if os.path.exists(self.bzapi.tokenfile):
            os.remove(self.bzapi.tokenfile)
        if os.path.exists(self.bzapi.cookiefile):
            os.remove(self.bzapi.cookiefile)

    def find_duplicates(self, *, title):
        try:
            issues = self.bzapi.query(self.bzapi.build_query(product=self.product,
                                                             status=['NEW', 'REOPENED', 'ASSIGNED'],
                                                             short_desc=title,
                                                             include_fields=['id', 'summary', 'weburl']))
            return [(issue.weburl, issue.summary) for issue in issues]
        except BugzillaError as e:
            raise TrackerError('Finding possible duplicates failed') from e

    def report_issue(self, *, title, body, product, product_version, component, blocks, test=None, extension='txt'):
        try:
            create_info = self.bzapi.build_createbug(summary=title,
                                                     description=body,
                                                     product=product,
                                                     version=product_version,
                                                     component=component,
                                                     blocks=blocks)

            bug = self.bzapi.createbug(create_info)
            if test:
                with BytesIO(test) as f:
                    self.bzapi.attachfile(idlist=bug.bug_id, attachfile=f, description='Test', is_patch=False, file_name='test.{ext}'.format(ext=extension))
            return bug.weburl
        except BugzillaError as e:
            raise TrackerError('Issue reporting failed') from e

    def settings(self):
        products = self.bzapi.getproducts(ptype='selectable')
        return {product['name']: dict(components=self.bzapi.getcomponents(product['name']),
                                      versions=[version['name'] for version in product['versions'] if version['is_active']])
                for product in products if product['components']}
