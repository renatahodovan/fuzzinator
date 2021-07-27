# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from io import BytesIO

from bugzilla import *

from .base import BaseTracker, TrackerError


class BugzillaTracker(BaseTracker):

    def __init__(self, product, url, api_key=None):
        self.product = product
        self.bzapi = Bugzilla(url, api_key=api_key)

        # Remove old token and cookie files since they may be outdated.
        if os.path.exists(self.bzapi.tokenfile):
            os.remove(self.bzapi.tokenfile)
        if os.path.exists(self.bzapi.cookiefile):
            os.remove(self.bzapi.cookiefile)

    def find_issue(self, query):
        try:
            issues = self.bzapi.query(self.bzapi.build_query(product=self.product,
                                                             status=['NEW', 'REOPENED', 'ASSIGNED'],
                                                             short_desc=query,
                                                             include_fields=['id', 'summary', 'weburl']))
            return [{'id': issue.bug_id, 'title': issue.summary, 'url': issue.weburl} for issue in issues]
        except BugzillaError as e:
            raise TrackerError('Finding possible duplicates failed') from e

    def report_issue(self, title, body, product, product_version, component, blocks, test=None, extension='txt'):
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
            return {'id': bug.bug_id, 'title': bug.summary, 'url': bug.weburl}
        except BugzillaError as e:
            raise TrackerError('Issue reporting failed') from e

    def settings(self):
        products = self.bzapi.getproducts(ptype='selectable')
        return {product['name']: dict(components=self.bzapi.getcomponents(product['name']),
                                      versions=[version['name'] for version in product['versions'] if version['is_active']])
                for product in products if product['components']}
