# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import os

import picire

from .picire_common import PicireReducer

logger = logging.getLogger(__name__)


class Picire(PicireReducer):
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
                 work_dir, **kwargs):

        super().__init__(parallel=parallel, combine_loops=combine_loops,
                         split_method=split_method, subset_first=subset_first, subset_iterator=subset_iterator, complement_iterator=complement_iterator,
                         jobs=jobs, max_utilization=max_utilization,
                         encoding=encoding, granularity=granularity, cache_class=cache_class, cleanup=cleanup,
                         work_dir=work_dir)

        self.atom = atom

    def __call__(self, *, sut_call, issue, on_job_progressed):
        logging.getLogger('picire').setLevel(logger.level)

        test, tester = self._prepare_call(sut_call=sut_call,
                                          issue=issue,
                                          on_job_progressed=on_job_progressed)

        try:
            reduced_file = picire.call(reduce_class=self.reduce_class,
                                       reduce_config=self.reduce_config,
                                       tester_class=tester.tester_class,
                                       tester_config=tester.tester_config,
                                       input=test.file_name,
                                       src=test.src,
                                       encoding=test.encoding,
                                       out=self.work_dir,
                                       atom=self.atom,
                                       granularity=self.granularity,
                                       cache_class=self.cache_class,
                                       cleanup=self.cleanup)
        except Exception as e:
            logger.warning('Exception in picire', exc_info=e)
            return None, list(tester.new_issues.values())

        with open(reduced_file, 'rb') as f:
            src = f.read()

        return src, list(tester.new_issues.values())
