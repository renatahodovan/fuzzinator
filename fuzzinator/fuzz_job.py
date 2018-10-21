# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import signal

from .call_job import CallJob
from .config import config_get_callable


class FuzzJob(CallJob):
    """
    Class for running fuzzer jobs.
    """

    def __init__(self, id, config, fuzzer_name, db, listener):
        CallJob.__init__(self, id, config, db, listener)
        fuzz_section = 'fuzz.' + fuzzer_name
        self.fuzzer_name = fuzzer_name
        self.sut_name = self.config.get(fuzz_section, 'sut')
        self.cost = int(self.config.get('sut.' + self.sut_name, 'cost', fallback=1))
        self.batch = float(self.config.get(fuzz_section, 'batch', fallback=1))
        self.refresh = float(self.config.get(fuzz_section, 'refresh', fallback=self.batch))

    def run(self):
        fuzzer, fuzzer_kwargs = config_get_callable(self.config, 'fuzz.' + self.fuzzer_name, 'fuzzer')

        # Register signal handler to catch keyboard interrupts.
        def terminate(signum, frame):
            fuzzer.__exit__(None, None, None)
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, terminate)

        index = 0
        issue_count = 0
        stat_updated = 0
        new_issues = []

        self.listener.update_fuzz_stat()
        with fuzzer:
            while index < self.batch:
                sut_call, sut_call_kwargs = config_get_callable(self.config, 'sut.' + self.sut_name, 'call')
                with sut_call:
                    while index < self.batch:
                        test = fuzzer(index=index, **fuzzer_kwargs)
                        if test is None:
                            self.batch = index
                            break

                        issue = sut_call(test=test, **sut_call_kwargs)

                        # Check if fuzzer maintains its own index.
                        if hasattr(fuzzer, 'index') and fuzzer.index > index:
                            index = fuzzer.index
                        else:
                            index += 1

                        # Check if fuzzer has its own test.
                        if hasattr(fuzzer, 'test'):
                            test = fuzzer.test

                        if issue and test is None:
                            self.batch = index
                            self.listener.warning(msg='{sut} crashed before the first test.'.format(sut=self.sut_name))
                            break

                        if issue is not None and ('test' not in issue or not issue['test']):
                            issue['test'] = test

                        if hasattr(fuzzer, 'feedback'):
                            fuzzer.feedback(issue)

                        if issue:
                            issue_count += 1

                        self.listener.job_progress(ident=self.id, progress=index)
                        if index - stat_updated >= self.refresh:
                            self.db.update_stat(self.sut_name, self.fuzzer_name, index - stat_updated, issue_count)
                            self.listener.update_fuzz_stat()
                            issue_count = 0
                            stat_updated = index

                        if issue:
                            self.add_issue(issue, new_issues=new_issues)
                            break

        # Update statistics.
        self.db.update_stat(self.sut_name, self.fuzzer_name, index - stat_updated, issue_count)
        self.listener.update_fuzz_stat()
        return new_issues
