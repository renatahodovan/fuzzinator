# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class BaseTracker(object):

    @property
    def logged_in(self):
        return True

    def find_issue(self, issue):
        pass

    def report_issue(self, **kwargs):
        pass

    def issue_url(self, issue):
        return ''
