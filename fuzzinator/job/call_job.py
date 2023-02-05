# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import hashlib


class CallJob(object):
    """
    Base class for jobs that call SUTs and can find new issues.
    """

    def __init__(self, id, config, subconfig_id, sut_name, fuzzer_name, db, listener):
        self.id = id
        self.config = config
        self.subconfig_id = subconfig_id
        self.sut_name = sut_name
        self.fuzzer_name = fuzzer_name
        self.db = db
        self.listener = listener

    def add_issue(self, issue, new_issues):
        test = issue['test']

        # Save issue details.
        issue.update(sut=self.sut_name,
                     fuzzer=self.fuzzer_name,
                     subconfig={'subconfig': self.subconfig_id},
                     test=test,
                     reduced=None,
                     reported=False)

        # Generate default hash ID for the test if does not exist.
        self.ensure_id(issue)

        # Save new issues.
        if self.db.add_issue(issue):
            new_issues.append(issue)
            self.listener.on_issue_added(job_id=self.id, issue=issue)
        else:
            self.listener.on_issue_updated(job_id=self.id, issue=issue)

    # Ensure that issue has an id, and if not, adds one
    def ensure_id(self, issue):
        if 'id' not in issue or not issue['id']:
            test = issue['test']
            hasher = hashlib.md5()
            hasher.update(test if isinstance(test, bytes) else str(test).encode('utf-8'))
            issue['id'] = hasher.hexdigest()
