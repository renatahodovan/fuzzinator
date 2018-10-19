# Copyright (c) 2017-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


from .call_job import CallJob
from .config import config_get_callable


class ValidateJob(CallJob):
    """
    Class for running test case validation jobs.
    """

    def __init__(self, config, issue, db, listener):
        super(ValidateJob, self).__init__(config=config, db=db, listener=listener)
        self.issue = issue
        self.sut_name = issue['sut']
        self.fuzzer_name = issue['fuzzer']
        self.cost = 0

    def run(self):
        sut_call, sut_call_kwargs = config_get_callable(self.config, 'sut.' + self.sut_name, ['validate_call', 'reduce_call', 'call'])

        with sut_call:
            sut_call_kwargs.update(self.issue)
            issue = sut_call(**sut_call_kwargs)
            if issue:
                issue['test'] = self.issue['test']
                if issue['id'] == self.issue['id']:
                    self.db.update_issue(self.issue, issue)
                    return [issue]

                self.add_issue(issue, new_issues=[])

        self.listener.invalid_issue(issue=self.issue)
        return []
