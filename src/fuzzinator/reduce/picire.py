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

      - ``split_class``, ``granularity``, ``subset_first``, ``subset_iterator``,
        ``complement_iterator``, ``parallel``, ``combine_loops``, ``jobs``,
        ``max_utilization``, ``atom``, ``encoding``, ``cache_class``

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

    def __init__(self, *,
                 split_class='zeller', granularity=2, subset_first=True, subset_iterator='forward', complement_iterator='forward',
                 parallel=False, combine_loops=False, jobs=os.cpu_count(), max_utilization=100,
                 atom='both',
                 encoding=None, cache_class='ContentCache',
                 **kwargs):

        super().__init__(split_class=split_class, granularity=granularity, subset_first=subset_first, subset_iterator=subset_iterator, complement_iterator=complement_iterator,
                         parallel=parallel, combine_loops=combine_loops, jobs=jobs, max_utilization=max_utilization,
                         encoding=encoding, cache_class=cache_class)

        self.atom = atom

    def __call__(self, *, sut_call, issue, on_job_progressed):
        logging.getLogger('picire').setLevel(logger.level)

        try:
            test, tester = self._prepare_call(sut_call=sut_call,
                                              issue=issue,
                                              on_job_progressed=on_job_progressed)

            out_src = picire.reduce(test.src,
                                    reduce_class=self.reduce_class, reduce_config=self.reduce_config,
                                    tester_class=tester.tester_class, tester_config=tester.tester_config,
                                    atom=self.atom,
                                    cache_class=self.cache_class)

            out_src = out_src.encode(test.encoding, errors='ignore')
            return out_src, list(tester.new_issues.values())
        except Exception as e:
            logger.warning('Exception in picire', exc_info=e)
            return None, list(tester.new_issues.values())
