# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import codecs
import picire


class PicireTester(object):

    def __init__(self, *, test_builder, test_pattern, sut_call, issue, on_job_progressed, encoding, new_issues):
        self._test_builder = test_builder
        self._test_pattern = test_pattern
        self._sut_call = sut_call
        self._issue = issue
        self._on_job_progressed = on_job_progressed
        self._encoding = encoding
        self._new_issues = new_issues

    def __call__(self, config, config_id):
        test = codecs.encode(self._test_builder(config), self._encoding, 'ignore')
        filename = self._test_pattern % '_'.join(str(i) for i in config_id)
        with self._sut_call:
            issue = self._sut_call(**dict(self._issue, test=test, filename=filename))

            # Second chance for flaky tests in case of 'assert' check.
            if config_id == 'assert' and not issue:
                issue = self._sut_call(**dict(self._issue, test=test, filename=filename))

            if issue:
                if self._issue['id'] == issue['id']:
                    # self._on_job_progressed(progress=len(str(test)))
                    return picire.AbstractDD.FAIL

                if 'test' not in issue or not issue['test']:
                    issue['test'] = test

                self._new_issues[issue['id']] = issue

        return picire.AbstractDD.PASS
