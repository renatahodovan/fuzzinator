# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from .call_job import CallJob
from .config import config_get_callable


class ReduceJob(CallJob):
    """
    Class for running test case reduction jobs.
    """

    def __init__(self, config, issue, work_dir, db, listener):
        CallJob.__init__(self, config, db, listener)
        self.issue = issue
        self.work_dir = work_dir

        self.sut_section = self.issue['sut']
        self.fuzzer_name = '{fuzzer}/{reducer}'.format(fuzzer=self.issue['fuzzer'].split('/')[0],
                                                       reducer=self.config.get(self.sut_section, 'reduce'))
        self.cost = int(self.config.get(self.sut_section, 'reduce_cost', fallback=self.config.get(self.sut_section, 'cost', fallback=1)))

    def run(self):
        if self.config.has_option(self.sut_section, 'reduce_call'):
            sut_call, sut_call_kwargs = config_get_callable(self.config, self.sut_section, 'reduce_call')
        else:
            sut_call, sut_call_kwargs = config_get_callable(self.config, self.sut_section, 'call')
        reduce, reduce_kwargs = config_get_callable(self.config, self.sut_section, 'reduce')

        with reduce:
            reduced_src, new_issues = reduce(sut_call=sut_call,
                                             sut_call_kwargs=sut_call_kwargs,
                                             listener=self.listener,
                                             ident=id(self),
                                             issue=self.issue,
                                             work_dir=os.path.join(self.work_dir, str(id(self))),
                                             **reduce_kwargs)

        if reduced_src is None:
            self.listener.warning(msg='Reduce of {ident} failed.'.format(ident=self.issue['id']))
        else:
            self.db.update_issue(self.issue, {'test': reduced_src, 'reduced': True})

        issues = list()
        for issue in new_issues:
            self.add_issue(issue, new_issues=issues)

        return issues
