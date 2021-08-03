# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import config_get_object
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
        subconfig_id = issue['subconfig'].get('subconfig') if isinstance(issue.get('subconfig'), dict) else None
        super().__init__(id, config, subconfig_id, sut_name, fuzzer_name, db, listener)

        self.issue = issue
        capacity = int(config.get('fuzzinator', 'cost_budget'))
        self.cost = min(int(config.get(sut_section, 'reduce_cost', fallback=config.get(sut_section, 'cost', fallback=1))), capacity)

    def run(self):
        valid, issues = ValidateJob(id=self.id,
                                    config=self.config,
                                    issue=self.issue,
                                    db=self.db,
                                    listener=self.listener).validate()
        if not valid:
            return issues

        sut_section = 'sut.' + self.sut_name
        sut_call = config_get_object(self.config, sut_section, ['reduce_call', 'call'])
        reduce = config_get_object(self.config, sut_section, 'reduce')

        reduced_src, new_issues = reduce(sut_call=sut_call,
                                         issue=self.issue,
                                         listener=self.listener,
                                         job_id=self.id)

        if reduced_src is None:
            self.listener.warning(job_id=self.id, msg='Reduce of {issue_id} failed.'.format(issue_id=self.issue['id']))
        else:
            self.db.update_issue_by_oid(self.issue['_id'], {'reduced': reduced_src})
            self.listener.on_issue_reduced(job_id=self.id, issue=self.issue)

        for issue in new_issues:
            self.add_issue(issue, new_issues=issues)

        return issues
