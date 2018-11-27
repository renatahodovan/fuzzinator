# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import codecs
import picire


class PicireTester(object):

    def __init__(self, *, test_builder, test_pattern, sut_call, sut_call_kwargs, enc, expected, listener, ident, issues):
        self._test_builder = test_builder
        self._test_pattern = test_pattern
        self._sut_call = sut_call
        self._sut_call_kwargs = sut_call_kwargs
        self._encoding = enc
        self._expected = expected
        self._listener = listener
        self._ident = ident
        self._issues = issues

    def __call__(self, config, config_id):
        test = codecs.encode(self._test_builder(config), self._encoding, 'ignore')
        with self._sut_call:
            filename = self._test_pattern % '_'.join(str(i) for i in config_id)
            issue = self._sut_call(test=test, filename=filename, **self._sut_call_kwargs)

            # Second chance for flaky tests in case of 'assert' check.
            if config_id == 'assert' and not issue:
                issue = self._sut_call(test=test, filename=filename, **self._sut_call_kwargs)

            if issue:
                if self._expected == issue['id']:
                    self._listener.job_progress(ident=self._ident, progress=len(test))
                    return picire.AbstractDD.FAIL

                if 'test' not in issue or not issue['test']:
                    issue['test'] = test

                self._issues[issue['id']] = issue

        return picire.AbstractDD.PASS
