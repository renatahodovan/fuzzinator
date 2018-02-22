# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import psutil
import shutil
import signal
import sys
import time
import traceback

from multiprocessing import Lock, Process, Queue

from .config import config_get_callable, config_get_kwargs, config_get_name_from_section, config_get_with_writeback, import_entity
from .fuzz_job import FuzzJob
from .listener import ListenerManager
from .mongo_driver import MongoDriver
from .reduce_job import ReduceJob
from .update_job import UpdateJob
from .validate_job import ValidateJob


class Controller(object):
    """
    Fuzzinator's main controller that orchestrates a fuzz session by scheduling
    all related activities (e.g., keeps SUTs up-to-date, runs fuzzers and feeds
    test cases to SUTs, or minimizes failure inducing test cases) . All
    configuration options of the framework must be encapsulated in a
    :class:`configparser.ConfigParser` object.

    The following config sections and options are recognized:

      - Section ``fuzzinator``: Global settings of the framework.

        - Option ``work_dir``: Work directory for temporary files. (Optional,
          default: ``~/.fuzzinator``)

        - Option ``db_uri``: URI to a MongoDB database to store found issues and
          execution statistics. (Optional, default:
          ``mongodb://localhost/fuzzinator``)

        - Option ``cost_budget``: (Optional, default: number of cpus)

      - Sections ``sut.NAME``: Definitions of a SUT named *NAME*

        - Option ``call``: Fully qualified name of a python callable that must
          accept a ``test`` keyword argument representing the input to the SUT
          and must return a dictionary object if the input triggered an issue in
          the SUT, or ``None`` otherwise. The returned issue dictionary (if any)
          *should* contain an ``'id'`` field that equals for issues that are not
          considered unique. (Mandatory)

          See package :mod:`fuzzinator.call` for potential callables.

        - Option ``cost``: (Optional, default: 1)

        - Option ``reduce``: Fully qualified name of a python callable that must
          accept ``issue``, ``sut_call``, ``sut_call_kwargs``, ``listener``,
          ``ident``, ``work_dir`` keyword arguments representing an issue to be
          reduced (and various other potentially needed objects), and must
          return a tuple consisting of a reduced test case for the issue (or
          ``None`` if the issue's current test case could not be reduced) and a
          (potentially empty) list of new issues that were discovered during
          test case reduction (if any). (Optional, no reduction for this SUT if
          option is missing.)

          See package :mod:`fuzzinator.reduce` for potential callables.

        - Option ``reduce_call``: Fully qualified name of a python callable that
          acts as the SUT's ``call`` option during test case reduction.
          (Optional, default: the value of option ``call``)

          See package :mod:`fuzzinator.call` for potential callables.

        - Option ``reduce_cost``: (Optional, default: the value of option
          ``cost``)

        - Option ``update_condition``: Fully qualified name of a python callable
          that must return ``True`` if and only if the SUT should be updated.
          (Optional, SUT is never updated if option is missing.)

          See package :mod:`fuzzinator.update` for potential callables.

        - Option ``update``: Fully qualified name of a python callable that
          should perform the update of the SUT. (Optional, SUT is never updated
          if option is missing.)

          See package :mod:`fuzzinator.update` for potential callables.

      - Sections ``fuzz.NAME``: Definitions of a fuzz job named *NAME*

        - Option ``sut``: Name of the SUT section that describes the subject of
          this fuzz job. (Mandatory)

        - Option ``fuzzer``: Fully qualified name of a python callable that must
          accept and ``index`` keyword argument representing a running counter
          in the fuzz job and must return a test input (or ``None``, which
          signals that the fuzzer is "exhausted" and cannot generate more test
          cases in this fuzz job). The semantics of the generated test input is
          not restricted by the framework, it is up to the configuration to
          ensure that the SUT of the fuzz job can deal with the tests generated
          by the fuzzer of the fuzz job. (Mandatory)

          See package :mod:`fuzzinator.fuzzer` for potential callables.

        - Option ``batch``: Number of times the fuzzer is requested to generate
          a new test and the SUT is called with it. (Optional, default: 1)

        - Option ``instances``: Number of instances of this fuzz job allowed to
          run in parallel. (Optional, default: ``inf``)

      - Callable options can be implemented as functions or classes with
        ``__call__`` method (the latter are instantiated first to get a callable
        object). Both constructor calls (if any) and the "real" calls can be
        given keyword arguments. These arguments have to be specified in
        sections ``(sut|fuzz).NAME.OPT[.init]`` with appropriate names (where
        the ``.init`` sections stand for the constructor arguments).

      - All callables can be decorated according to python semantics. The
        decorators must be callable classes themselves and have to be specified
        in options ``OPT.decorate(N)`` with fully qualified name. Multiple
        decorators can be applied to a callable ``OPT``, their order is
        specified by an integer index in parentheses. Keyword arguments to be
        passed to the decorators have to be listed in sections
        ``(sut|fuzz).NAME.OPT.decorate(N)``.

        See packages :mod:`fuzzinator.call` and :mod:`fuzzinator.fuzzer` for
        potential decorators.
    """

    def __init__(self, config):
        """
        :param configparser.ConfigParser config: the configuration options of the
            fuzz session.

        :ivar fuzzinator.ListenerManager listener: a listener manager object that is
            called on various events during the fuzz session.
        """
        self.config = config

        # Extract sections describing fuzzing jobs.
        self.fuzzers = [section for section in config.sections() if section.startswith('fuzz.') and section.count('.') == 1]

        self.capacity = int(config_get_with_writeback(self.config, 'fuzzinator', 'cost_budget', str(os.cpu_count())))
        self.work_dir = config_get_with_writeback(self.config, 'fuzzinator', 'work_dir', os.path.join(os.getcwd(), '.fuzzinator'))

        self.db = MongoDriver(config_get_with_writeback(self.config, 'fuzzinator', 'db_uri', 'mongodb://localhost/fuzzinator'))
        self.db.init_db([(self.config.get(fuzzer, 'sut'), config_get_name_from_section(fuzzer)) for fuzzer in self.fuzzers])

        self.listener = ListenerManager()
        for name in config_get_kwargs(self.config, 'listeners'):
            entity = import_entity(self.config.get('listeners', name))
            self.listener += entity(**config_get_kwargs(config, 'listeners.' + name + '.init'))

        self._issue_queue = Queue()
        self._lock = Lock()

    def run(self, *, max_cycles=None):
        """
        Start the fuzz session.

        :param int max_cycles: maximum number to iterate through the fuzz jobs
            defined in the configuration (defaults to ``inf``).
        """
        max_cycles = max_cycles if max_cycles is not None else float('inf')
        cycle = 0
        running_jobs = dict()
        fuzz_idx = 0
        try:
            while True:
                if fuzz_idx == 0:
                    cycle += 1
                if cycle > max_cycles or (not self.fuzzers and max_cycles != float('inf')):
                    self._wait_for_load(self.capacity, running_jobs)
                    break

                next_job = None
                if not self._issue_queue.empty():

                    # Perform all the reduce jobs before start hunting for new issues.
                    while not self._issue_queue.empty():
                        issue = self._issue_queue.get_nowait()
                        if self.config.has_option(issue['sut'], 'reduce'):
                            next_job = ReduceJob(config=self.config,
                                                 issue=issue,
                                                 work_dir=self.work_dir,
                                                 db=self.db,
                                                 listener=self.listener)
                            next_job_id = id(next_job)
                            self.listener.new_reduce_job(ident=next_job_id,
                                                         sut=config_get_name_from_section(next_job.sut_section),
                                                         cost=next_job.cost,
                                                         issue_id=issue['id'],
                                                         size=len(issue['test']))
                            break

                if not next_job:
                    if not self.fuzzers:
                        self._wait_for_load(0, running_jobs)
                        time.sleep(1)
                        continue

                    fuzzer_name = config_get_name_from_section(self.fuzzers[fuzz_idx])
                    instances = self.config.get(self.fuzzers[fuzz_idx], 'instances', fallback='inf')
                    instances = float(instances) if instances == 'inf' else int(instances)
                    if instances <= len(list(filter(lambda job: job.fuzzer_name == fuzzer_name, (running_jobs[ident]['job'] for ident in running_jobs if isinstance(running_jobs[ident]['job'], FuzzJob))))):
                        # Update fuzz_idx to point the next job's parameters.
                        fuzz_idx = (fuzz_idx + 1) % len(self.fuzzers)
                        continue

                    next_job = FuzzJob(config=self.config,
                                       fuzz_section=self.fuzzers[fuzz_idx],
                                       db=self.db,
                                       listener=self.listener)
                    next_job_id = id(next_job)

                    # Before starting a new fuzz job let's check if we are working with
                    # the latest version of the SUT and update it if needed.
                    self._check_update(next_job, running_jobs)

                    # Update fuzz_idx to point the next job's parameters.
                    fuzz_idx = (fuzz_idx + 1) % len(self.fuzzers)

                    # Notify the active listener about the new job.
                    self.listener.new_fuzz_job(ident=next_job_id,
                                               fuzzer=config_get_name_from_section(next_job.fuzz_section),
                                               sut=config_get_name_from_section(next_job.sut_section),
                                               cost=next_job.cost,
                                               batch=next_job.batch)

                # Wait until there is enough capacity for the next job.
                self._wait_for_load(next_job.cost, running_jobs)

                proc = Process(target=self._run_job, args=(next_job,))
                running_jobs[next_job_id] = dict(job=next_job, proc=proc)
                # Notify the active listener that a job has been activated.
                self.listener.activate_job(ident=next_job_id)
                proc.start()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.listener.warning(msg='{msg}\n{trace}'.format(msg=str(e), trace=traceback.format_exc()))
        finally:
            Controller.kill_process_tree(os.getpid(), kill_root=False)
            if os.path.exists(self.work_dir):
                shutil.rmtree(self.work_dir, ignore_errors=True)

    def _check_update(self, job, running_jobs):
        if self.config.has_option(job.sut_section, 'update_condition') and \
                self.config.has_option(job.sut_section, 'update'):
            update_condition, update_condition_kwargs = config_get_callable(self.config, job.sut_section, 'update_condition')
            with update_condition:
                if update_condition(**update_condition_kwargs):
                    next_job = UpdateJob(config=self.config,
                                         sut_section=job.sut_section)
                    next_job_id = id(next_job)
                    self.listener.new_update_job(ident=next_job_id,
                                                 sut=config_get_name_from_section(next_job.sut_section))
                    # Wait until every job has finished.
                    self._wait_for_load(self.capacity, running_jobs)
                    # Emit 'next_job available' event.
                    self.listener.activate_job(ident=next_job_id)
                    # Update job runs in the main thread since it's blocking for any other jobs.
                    next_job.run()
                    self.listener.remove_job(ident=next_job_id)

    def _wait_for_load(self, new_load, running_jobs):
        while True:
            load = 0
            for ident in list(running_jobs):
                if not running_jobs[ident]['proc'].is_alive():
                    self.listener.remove_job(ident=ident)
                    del running_jobs[ident]
                else:
                    load += running_jobs[ident]['job'].cost
            self.listener.update_load(load=load)
            if load + new_load <= self.capacity:
                return load
            time.sleep(1)

    def _run_job(self, job):
        try:
            for issue in job.run():
                self.add_reduce_job(issue=issue)
        except Exception as e:
            self.listener.warning(msg='Exception: {job} {exception}\n{trace}'.format(
                job=repr(job),
                exception=e,
                trace=''.join(traceback.format_exception(*sys.exc_info())).strip('\n')))

    def add_reduce_job(self, issue):
        with self._lock:
            self._issue_queue.put(issue)

    def reduce_all(self):
        for issue in self.db.find_issues_by_suts([section for section in self.config.sections() if section.startswith('sut.') and section.count('.') == 1]):
            if not issue['reported'] and not issue['reduced']:
                self.add_reduce_job(issue)

    def validate(self, issue):
        ValidateJob(config=self.config,
                    issue=issue,
                    db=self.db,
                    listener=self.listener).run()

    @staticmethod
    def kill_process_tree(pid, kill_root=True, sig=signal.SIGTERM):
        try:
            root_proc = psutil.Process(pid)
            children = root_proc.children(recursive=True)
            if kill_root:
                children.append(root_proc)
            for proc in children:
                # Would be easier to use proc.terminate() here but psutils
                # (up to version 5.4.0) on Windows terminates processes with
                # the 0 signal/code, making the outcome of the terminated
                # process indistinguishable from a successful execution.
                try:
                    os.kill(proc.pid, sig)
                except OSError:
                    pass
            psutil.wait_procs(children, timeout=1)
        except psutil.NoSuchProcess:
            pass
