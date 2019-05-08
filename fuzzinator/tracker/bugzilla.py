# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from io import BytesIO

from bugzilla import *

from .base import BaseTracker


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
        return self.bzapi.query(self.bzapi.build_query(product=self.product,
                                                       status=['NEW', 'REOPENED', 'ASSIGNED'],
                                                       short_desc=query,
                                                       include_fields=['id', 'summary', 'weburl']))

    def report_issue(self, title, body, product, product_version, component, blocks, test, extension='txt'):
        create_info = self.bzapi.build_createbug(summary=title,
                                                 description=body,
                                                 product=product,
                                                 version=product_version,
                                                 component=component,
                                                 blocks=blocks)

        bug = self.bzapi.createbug(create_info)
        with BytesIO(test) as f:
            self.bzapi.attachfile(idlist=bug.bug_id, attachfile=f, description='Test', is_patch=False, file_name='test.{ext}'.format(ext=extension))
        return bug

    def __call__(self, issue):
        pass

    def issue_url(self, issue):
        return issue.weburl

    def product_info(self):
        products = self.bzapi.product_get(ptype='selectable')
        return {product['name']: dict(components=self.bzapi.getcomponents(product),
                                      versions=[version['name'] for version in product['versions'] if version['is_active']])
                for product in products if product['components']}
