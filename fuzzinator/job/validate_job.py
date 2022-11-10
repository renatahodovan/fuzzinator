# Copyright (c) 2017-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from datetime import datetime

from ..config import config_get_object
from .call_job import CallJob


class ValidateJob(CallJob):
    """
    Class for running test case validation jobs.
    """

    def __init__(self, id, config, issue, db, listener):
        sut_name = issue['sut']
        sut_section = f'sut.{sut_name}'
        fuzzer_name = issue['fuzzer']
        subconfig_id = issue['subconfig'].get('subconfig') if isinstance(issue.get('subconfig'), dict) else None
        super().__init__(id, config, subconfig_id, sut_name, fuzzer_name, db, listener)

        self.issue = issue
        capacity = int(config.get('fuzzinator', 'cost_budget'))
        self.cost = min(int(config.get(sut_section, 'validate_cost', fallback=config.get(sut_section, 'cost', fallback=1))), capacity)

    def run(self):
        _, new_issues = self.validate()
        return new_issues

    def validate(self):
        sut_call = config_get_object(self.config, f'sut.{self.sut_name}', ['validate_call', 'call'])
        with sut_call:
            issue = sut_call(**self.issue)

        new_issues = []

        if issue:
            issue['test'] = self.issue['test']

            self.ensure_id(issue)
            if issue['id'] == self.issue['id'] and not self.issue.get('invalid'):
                self.db.update_issue_by_oid(self.issue['_id'], issue)
                return True, new_issues

            self.add_issue(issue, new_issues=new_issues)

        if not self.issue.get('invalid'):
            self.db.update_issue_by_oid(self.issue['_id'], {'invalid': datetime.utcnow()})
            self.listener.on_issue_invalidated(job_id=self.id, issue=self.issue)

        return False, new_issues
