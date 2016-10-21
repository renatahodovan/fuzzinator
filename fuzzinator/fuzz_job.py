# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import signal

from .call_job import CallJob
from .config import config_get_callable, config_get_name_from_section


class FuzzJob(CallJob):
    """
    Class for running fuzzer jobs.
    """

    def __init__(self, config, fuzz_section, db, listener):
        CallJob.__init__(self, config, db, listener)
        self.fuzz_section = fuzz_section

        self.sut_section = self.config.get(self.fuzz_section, 'sut')
        self.fuzzer_name = config_get_name_from_section(self.fuzz_section)
        self.cost = int(self.config.get(self.sut_section, 'cost', fallback=1))
        self.batch = float(self.config.get(self.fuzz_section, 'batch', fallback=1))

    def run(self):
        fuzzer, fuzzer_kwargs = config_get_callable(self.config, self.fuzz_section, 'fuzzer')

        # Register signal handler to catch keyboard interrupts.
        def terminate(signum, frame):
            fuzzer.__exit__(None, None, None)
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, terminate)

        index = 0
        issue_count = 0
        new_issues = []

        self.listener.update_fuzz_stat()
        with fuzzer:
            while index < self.batch:
                sut_call, sut_call_kwargs = config_get_callable(self.config, self.sut_section, 'call')
                with sut_call:
                    while index < self.batch:
                        test = fuzzer(index=index, **fuzzer_kwargs)
                        if not test:
                            self.batch = index
                            break

                        issue = sut_call(test=test, **sut_call_kwargs)

                        # Check if fuzzer maintains its own index.
                        if hasattr(fuzzer, 'index') and fuzzer.index > index:
                            index = fuzzer.index
                        else:
                            index += 1
                        self.listener.job_progress(ident=id(self), progress=index)

                        if issue:
                            issue_count += 1

                            # Check if fuzzer has its own test.
                            if hasattr(fuzzer, 'test'):
                                test = fuzzer.test
                                if not test:
                                    self.batch = index
                                    self.listener.warning(msg='{sut} crashed before the first test.'.format(sut=config_get_name_from_section(self.sut_section)))
                                    break

                            if 'test' not in issue or not issue['test']:
                                issue['test'] = test

                            self.add_issue(issue, new_issues=new_issues)
                            break

        # Update statistics.
        self.db.update_stat(self.sut_section, self.fuzzer_name, self.batch, issue_count)
        self.listener.update_fuzz_stat()
        return new_issues
