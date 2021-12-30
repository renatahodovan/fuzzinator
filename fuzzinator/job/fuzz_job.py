# Copyright (c) 2016-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import signal
import time

from ..config import config_get_object
from .call_job import CallJob


class FuzzJob(CallJob):
    """
    Class for running fuzzer jobs.
    """

    def __init__(self, id, config, subconfig_id, fuzzer_name, db, listener):
        fuzz_section = 'fuzz.' + fuzzer_name
        sut_name = config.get(fuzz_section, 'sut')
        super().__init__(id, config, subconfig_id, sut_name, fuzzer_name, db, listener)

        capacity = int(config.get('fuzzinator', 'cost_budget'))
        self.cost = min(int(config.get('sut.' + sut_name, 'cost', fallback=1)), capacity)
        self.batch = float(config.get(fuzz_section, 'batch', fallback=1))
        self.refresh = float(config.get(fuzz_section, 'refresh', fallback=self.batch))

    def run(self):
        fuzzer = config_get_object(self.config, 'fuzz.' + self.fuzzer_name, 'fuzzer')

        # Register signal handler to catch keyboard interrupts.
        def terminate(signum, frame):
            fuzzer.__exit__(None, None, None)
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, terminate)

        index = 0
        issue_count = 0
        start_time = time.time()
        stat_updated = 0
        new_issues = []

        self.listener.on_stats_updated()
        with fuzzer:
            while index < self.batch:
                sut_call = config_get_object(self.config, 'sut.' + self.sut_name, 'call')
                with sut_call:
                    while index < self.batch:
                        test = fuzzer(index=index)
                        if test is None:
                            self.batch = index
                            break

                        issue = sut_call(test=test)

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
                            self.listener.warning(job_id=self.id, msg='{sut} crashed before the first test.'.format(sut=self.sut_name))
                            break

                        if issue is not None and ('test' not in issue or not issue['test']):
                            issue['test'] = test

                        if hasattr(fuzzer, 'feedback'):
                            fuzzer.feedback(issue)

                        if issue:
                            issue_count += 1

                        if index - stat_updated >= self.refresh:
                            self.listener.on_job_progressed(job_id=self.id, progress=index)
                            self.db.update_stat(self.sut_name, self.fuzzer_name, self.subconfig_id, index - stat_updated, issue_count, time.time() - start_time)
                            self.listener.on_stats_updated()
                            issue_count = 0
                            start_time = time.time()
                            stat_updated = index

                        if issue:
                            self.add_issue(issue, new_issues=new_issues)
                            break

        # Update statistics.
        self.db.update_stat(self.sut_name, self.fuzzer_name, self.subconfig_id, index - stat_updated, issue_count, time.time() - start_time)
        self.listener.on_stats_updated()
        return new_issues
