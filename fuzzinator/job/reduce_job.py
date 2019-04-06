# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os

from ..config import config_get_callable
from .call_job import CallJob
from .validate_job import ValidateJob


class ReduceJob(CallJob):
    """
    Class for running test case reduction jobs.
    """

    def __init__(self, id, config, issue, db, listener):
        sut_name = issue['sut']
        sut_section = 'sut.' + sut_name
        fuzzer_name = '{fuzzer}/{reducer}'.format(fuzzer=issue['fuzzer'].split('/')[0],
                                                  reducer=config.get(sut_section, 'reduce'))
        super().__init__(id, config, sut_name, fuzzer_name, db, listener)

        self.issue = issue
        self.cost = int(config.get(sut_section, 'reduce_cost', fallback=config.get(sut_section, 'cost', fallback=1)))
        self.work_dir = config.get('fuzzinator', 'work_dir')

    def run(self):
        valid, issues = ValidateJob(id=self.id,
                                    config=self.config,
                                    issue=self.issue,
                                    db=self.db,
                                    listener=self.listener).validate()
        if not valid:
            return issues

        sut_section = 'sut.' + self.sut_name
        sut_call, sut_call_kwargs = config_get_callable(self.config, sut_section, ['reduce_call', 'call'])
        reduce, reduce_kwargs = config_get_callable(self.config, sut_section, 'reduce')

        with reduce:
            reduced_src, new_issues = reduce(sut_call=sut_call,
                                             sut_call_kwargs=sut_call_kwargs,
                                             listener=self.listener,
                                             ident=self.id,
                                             issue=self.issue,
                                             work_dir=os.path.join(self.work_dir, str(self.id)),
                                             **reduce_kwargs)

        if reduced_src is None:
            self.listener.warning(ident=self.id, msg='Reduce of {ident} failed.'.format(ident=self.issue['id']))
        else:
            self.db.update_issue(self.issue, {'reduced': reduced_src})
            self.listener.update_issue(ident=self.id, issue=self.issue)

        for issue in new_issues:
            self.add_issue(issue, new_issues=issues)

        return issues
