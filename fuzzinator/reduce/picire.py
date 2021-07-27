# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os

import chardet
import picire

from ..config import as_bool, as_int_or_inf
from .picire_tester import PicireTester
from .reducer import Reducer

logger = logging.getLogger(__name__)


class Picire(Reducer):
    """
    Test case reducer based on the Picire Parallel Delta Debugging Framework.

    **Optional parameters of the reducer:**

      - ``parallel``, ``combine_loops``, ``split_method``, ``subset_first``,
        ``subset_iterator``, ``complement_iterator``, ``jobs``,
        ``max_utilization``, ``encoding``, ``atom``, ``granularity``,
        ``cache_class``, ``cleanup``

    Refer to https://github.com/renatahodovan/picire for configuring Picire.

    Note: This reducer is capable of detecting new issues found during the test
    reduction (if any).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            #call=...
            cost=1
            reduce=fuzzinator.reduce.Picire
            reduce_cost=4

            [sut.foo.reduce]
            parallel=True
            jobs=4
            subset_iterator=skip
    """

    def __init__(self, *, parallel=False, combine_loops=False,
                 split_method='zeller', subset_first=True, subset_iterator='forward', complement_iterator='forward',
                 jobs=os.cpu_count(), max_utilization=100,
                 atom='both',
                 encoding=None, granularity=2, cache_class='ContentCache', cleanup=True,
                 **kwargs):
        parallel = as_bool(parallel)
        combine_loops = as_bool(combine_loops)
        split_method = getattr(picire.config_splitters, split_method)
        subset_first = as_bool(subset_first)
        subset_iterator = getattr(picire.config_iterators, subset_iterator)
        complement_iterator = getattr(picire.config_iterators, complement_iterator)
        jobs = int(jobs) if parallel else 1
        max_utilization = int(max_utilization)

        self.atom = atom

        self.encoding = encoding
        self.granularity = as_int_or_inf(granularity)
        self.cache_class = getattr(picire, cache_class)
        if parallel:
            self.cache_class = picire.shared_cache_decorator(self.cache_class)
        self.cleanup = as_bool(cleanup)

        # Choose the reducer class that will be used and its configuration.
        self.reduce_config = {'split': split_method}
        if not parallel:
            self.reduce_class = picire.LightDD
            self.reduce_config['subset_iterator'] = subset_iterator
            self.reduce_config['complement_iterator'] = complement_iterator
            self.reduce_config['subset_first'] = subset_first
        else:
            self.reduce_config['proc_num'] = jobs
            self.reduce_config['max_utilization'] = max_utilization

            if combine_loops:
                self.reduce_class = picire.CombinedParallelDD
                self.reduce_config['config_iterator'] = picire.CombinedIterator(subset_first, subset_iterator, complement_iterator)
            else:
                self.reduce_class = picire.ParallelDD
                self.reduce_config['subset_iterator'] = subset_iterator
                self.reduce_config['complement_iterator'] = complement_iterator
                self.reduce_config['subset_first'] = subset_first

    def __call__(self, *, sut_call, issue, listener, ident, work_dir):
        logging.getLogger('picire').setLevel(logger.level)

        src = issue['test']
        if isinstance(src, bytes):
            encoding = self.encoding or chardet.detect(src)['encoding'] or 'latin-1'
        else:
            encoding = self.encoding or 'latin-1'
            src = src.encode(encoding, errors='ignore')

        file_name = issue.get('filename', 'test')

        new_issues = dict()
        tester_config = dict(
            sut_call=sut_call,
            issue=issue,
            listener=listener,
            ident=ident,
            encoding=encoding,
            new_issues=new_issues,
        )

        call_config = dict(
            reduce_class=self.reduce_class,
            reduce_config=self.reduce_config,
            tester_class=PicireTester,
            tester_config=tester_config,
            input=file_name,
            src=src,
            encoding=encoding,
            out=work_dir,
            atom=self.atom,
            granularity=self.granularity,
            cache_class=self.cache_class,
            cleanup=self.cleanup,
        )

        try:
            reduced_file = picire.call(**call_config)
        except Exception as e:
            logger.warning('Exception in picire', exc_info=e)
            return None, list(new_issues.values())

        with open(reduced_file, 'rb') as f:
            src = f.read()

        return src, list(new_issues.values())
