# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import codecs

from collections import namedtuple
from os.path import join

import chardet
import picire

from ..config import as_bool, as_int_or_inf
from .reducer import Reducer


class PicireTester(object):

    def __init__(self, *, test_builder, sut_call, issue, on_job_progressed, filename, encoding, new_issues):
        self._test_builder = test_builder
        self._sut_call = sut_call
        self._issue = issue
        self._on_job_progressed = on_job_progressed
        self._filename = filename
        self._encoding = encoding
        self._new_issues = new_issues

    def __call__(self, config, config_id):
        test = codecs.encode(self._test_builder(config), self._encoding, 'ignore')
        filename = join('_'.join(str(i) for i in config_id), self._filename)
        with self._sut_call:
            issue = self._sut_call(**dict(self._issue, test=test, filename=filename))

            # Second chance for flaky tests in case of 'assert' check.
            if 'assert' in config_id and not issue:
                issue = self._sut_call(**dict(self._issue, test=test, filename=filename))

            if issue:
                if self._issue['id'] == issue['id']:
                    # self._on_job_progressed(progress=len(str(test)))
                    return picire.Outcome.FAIL

                if 'test' not in issue or not issue['test']:
                    issue['test'] = test

                self._new_issues[issue['id']] = issue

        return picire.Outcome.PASS


class PicireReducer(Reducer):

    def __init__(self, *,
                 split_class, granularity, subset_first, subset_iterator, complement_iterator,
                 parallel, combine_loops, jobs, max_utilization,
                 encoding, cache_class):
        split_class = getattr(picire.config_splitters, split_class)
        granularity = as_int_or_inf(granularity)
        subset_first = as_bool(subset_first)
        subset_iterator = getattr(picire.config_iterators, subset_iterator)
        complement_iterator = getattr(picire.config_iterators, complement_iterator)
        parallel = as_bool(parallel)
        combine_loops = as_bool(combine_loops)
        jobs = int(jobs) if parallel else 1
        max_utilization = int(max_utilization)

        self.encoding = encoding
        self.cache_class = getattr(picire, cache_class)
        if parallel:
            self.cache_class = picire.shared_cache_decorator(self.cache_class)

        # Choose the reducer class that will be used and its configuration.
        if not parallel:
            self.reduce_class = picire.DD
            self.reduce_config = dict(subset_iterator=subset_iterator,
                                      complement_iterator=complement_iterator,
                                      subset_first=subset_first)
        else:
            if combine_loops:
                self.reduce_class = picire.CombinedParallelDD
                self.reduce_config = dict(config_iterator=picire.CombinedIterator(subset_first, subset_iterator, complement_iterator))
            else:
                self.reduce_class = picire.ParallelDD
                self.reduce_config = dict(subset_iterator=subset_iterator,
                                          complement_iterator=complement_iterator,
                                          subset_first=subset_first)
            self.reduce_config.update(dict(proc_num=jobs,
                                           max_utilization=max_utilization))
        self.reduce_config.update(dict(split=split_class(n=granularity)))

    TestTuple = namedtuple('TestTuple', ['src', 'encoding'])
    TesterTuple = namedtuple('TesterTuple', ['tester_class', 'tester_config', 'new_issues'])

    def _prepare_call(self, *, sut_call, issue, on_job_progressed):
        src = issue['test']
        if isinstance(src, bytes):
            encoding = self.encoding or chardet.detect(src)['encoding'] or 'latin-1'
            src = src.decode(encoding)
        else:
            encoding = self.encoding or 'latin-1'

        new_issues = dict()
        tester_config = dict(sut_call=sut_call,
                             issue=issue,
                             on_job_progressed=on_job_progressed,
                             filename=issue.get('filename', 'test'),
                             encoding=encoding,
                             new_issues=new_issues)

        return self.TestTuple(src, encoding), self.TesterTuple(PicireTester, tester_config, new_issues)
