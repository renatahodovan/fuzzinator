# Copyright (c) 2017-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from datetime import datetime

from ..config import config_get_callable
from .call_job import CallJob


class ValidateJob(CallJob):
    """
    Class for running test case validation jobs.
    """

    def __init__(self, id, config, issue, db, listener):
        sut_name = issue['sut']
        fuzzer_name = issue['fuzzer']
        subconfig_id = issue['subconfig'].get('subconfig') if isinstance(issue.get('subconfig'), dict) else None
        super().__init__(id, config, subconfig_id, sut_name, fuzzer_name, db, listener)

        self.issue = issue
        self.cost = int(config.get('sut.' + sut_name, 'validate_cost', fallback=config.get('sut.' + sut_name, 'cost', fallback=1)))

    def run(self):
        _, new_issues = self.validate()
        return new_issues

    def validate(self):
        sut_call, sut_call_kwargs = config_get_callable(self.config, 'sut.' + self.sut_name, ['validate_call', 'reduce_call', 'call'])

        with sut_call:
            sut_call_kwargs.update(self.issue)
            issue = sut_call(**sut_call_kwargs)

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
            self.listener.on_issue_invalidated(ident=self.id, issue=self.issue)

        return False, new_issues
