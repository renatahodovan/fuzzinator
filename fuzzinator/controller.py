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
import time
import traceback

from multiprocessing import Lock, Process, Queue

from .config import config_get_callable, config_get_kwargs, config_get_name_from_section, config_get_with_writeback, import_entity
from .job import FuzzJob, ReduceJob, UpdateJob, ValidateJob
from .listener import ListenerManager
from .mongo_driver import MongoDriver


class Controller(object):
    """
    Fuzzinator's main controller that orchestrates a fuzz session by scheduling
    all related activities (e.g., keeps SUTs up-to-date, runs fuzzers and feeds
    test cases to SUTs, or minimizes failure inducing test cases). All
    configuration options of the framework must be encapsulated in a
    :class:`configparser.ConfigParser` object.

    The following config sections and options are recognized:

      - Section ``fuzzinator``: Global settings of the framework.

        - Option ``work_dir``: Pattern of work directory for temporary files,
          which may contain the substring ``{uid}`` as a placeholder for a
          unique string (replaced by the framework). (Optional, default:
          ``~/.fuzzinator-{uid}``)

        - Option ``db_uri``: URI to a MongoDB database to store found issues and
          execution statistics. (Optional, default:
          ``mongodb://localhost/fuzzinator``)

        - Option ``cost_budget``: (Optional, default: number of cpus)

      - Sections ``sut.NAME``: Definitions of a SUT named *NAME*

        - Option ``call``: Fully qualified name of a python callable that must
          accept a ``test`` keyword argument representing the input to the SUT
          and must return a dictionary object if the input triggered an issue
          in the SUT, or a value considered false otherwise (which can be a
          simple ``None``, but can also be a ``NonIssue`` in complex cases).
          The returned issue dictionary (if any) *should* contain an ``'id'``
          field that equals for issues that are not considered unique.
          (Mandatory)

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

        - Option ``validate_call``: Fully qualified name of a python callable
          that acts as the SUT's ``call`` option during test case validation.
          (Optional, default: the value of option ``reduce_call`` if defined,
          otherwise the value of option ``call``)

          See package :mod:`fuzzinator.call` for potential callables.

        - Option ``validate_cost``: (Optional, default: the value of option
          ``cost``)

        - Option ``update_condition``: Fully qualified name of a python callable
          that must return ``True`` if and only if the SUT should be updated.
          (Optional, SUT is never updated automatically if option is missing.)

          See package :mod:`fuzzinator.update` for potential callables.

        - Option ``update``: Fully qualified name of a python callable that
          should perform the update of the SUT. (Optional, SUT is never updated
          if option is missing.)

          See package :mod:`fuzzinator.update` for potential callables.

        - Option ``update_cost``: (Optional, default: the value of option
          ``fuzzinator:cost_budget``)

        - Option ``formatter``: Fully qualified name of a python callable that
          formats the issue dictionary of the SUT and returns a custom string
          representation. It must accept ``issue`` and ``format`` keyword
          arguments representing an issue to be formatted and a formatting
          instruction. If ``format`` is ``'long'`` or not specified, the issue
          should be formatted in full, while if ``'short'`` is given, a
          summary description (preferably a single line of text) should be
          returned.
          (Optional, default: :func:`fuzzinator.formatter.JsonFormatter`.)

          See package :mod:`fuzzinator.formatter` for further potential
          callables.

        - Option ``tui_formatter``: Fully qualified name of a python
          callable that formats the issue dictionary of the SUT to display
          it in the TUI issue viewer interface.
          (Optional, default: the value of option ``formatter``)

          See package :mod:`fuzzinator.formatter` for further potential
          callables.

        - Option ``email_formatter``: Fully qualified name of a python
          callable that formats the issue dictionary of the SUT to insert
          it into an e-mail notification.
          (Optional, default: the value of option ``formatter``)

          See package :mod:`fuzzinator.formatter` for further potential
          callables.

      - Sections ``fuzz.NAME``: Definitions of a fuzz job named *NAME*

        - Option ``sut``: Name of the SUT that describes the subject of
          this fuzz job. (Mandatory)

        - Option ``fuzzer``: Fully qualified name of a python callable that must
          accept an ``index`` keyword argument representing a running counter
          in the fuzz job and must return a test input (or ``None``, which
          signals that the fuzzer is "exhausted" and cannot generate more test
          cases in this fuzz job). The semantics of the generated test input is
          not restricted by the framework, it is up to the configuration to
          ensure that the SUT of the fuzz job can deal with the tests generated
          by the fuzzer of the fuzz job. (Mandatory)

          See package :mod:`fuzzinator.fuzzer` for potential callables.

        - Option ``batch``: Number of times the fuzzer is requested to generate
          a new test for the SUT. (Optional, default: 1)

        - Option ``instances``: Number of instances of this fuzz job allowed to
          run in parallel. (Optional, default: ``inf``)

        - Option ``refresh``: Statistics update frequency in terms of executed
          test cases. (Optional, default: ``batch`` size)

      - Section ``listeners``: Definitions of custom event listeners.
        This section is optional.

        - Options ``OPT``: Fully qualified name of a python class that
          executes custom actions for selected events.

        See package :mod:`fuzzinator.listeners` for potential listeners.

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

        # Extract fuzzer names from sections describing fuzzing jobs.
        self.fuzzers = [config_get_name_from_section(section) for section in config.sections() if section.startswith('fuzz.') and section.count('.') == 1]

        self.capacity = int(config_get_with_writeback(self.config, 'fuzzinator', 'cost_budget', str(os.cpu_count())))
        self.work_dir = config_get_with_writeback(self.config, 'fuzzinator', 'work_dir', os.path.join(os.getcwd(), '.fuzzinator-{uid}')).format(uid=os.getpid())
        self.config.set('fuzzinator', 'work_dir', self.work_dir)

        self.db = MongoDriver(config_get_with_writeback(self.config, 'fuzzinator', 'db_uri', 'mongodb://localhost/fuzzinator'))
        self.db.init_db([(self.config.get('fuzz.' + fuzzer, 'sut'), fuzzer) for fuzzer in self.fuzzers])

        self.listener = ListenerManager()
        for name in config_get_kwargs(self.config, 'listeners'):
            entity = import_entity(self.config.get('listeners', name))
            self.listener += entity(config=config, **config_get_kwargs(config, 'listeners.' + name + '.init'))

        self._shared_queue = Queue()
        self._shared_lock = Lock()

    def run(self, *, max_cycles=None):
        """
        Start the fuzz session.

        :param int max_cycles: maximum number to iterate through the fuzz jobs
            defined in the configuration (defaults to ``inf``).
        """
        max_cycles = max_cycles if max_cycles is not None else float('inf')
        cycle = 0
        fuzz_idx = 0
        load = 0
        job_id = 0
        job_queue = []
        running_jobs = dict()

        def _update_load():
            current_load = 0
            for ident in list(running_jobs):
                if not running_jobs[ident]['proc'].is_alive() or not psutil.pid_exists(running_jobs[ident]['proc'].pid):
                    self.listener.remove_job(ident=ident)
                    del running_jobs[ident]
                else:
                    current_load += running_jobs[ident]['job'].cost

            nonlocal load
            if load != current_load:
                load = current_load
                self.listener.update_load(load=load)

        def _poll_jobs():
            with self._shared_lock:
                while not self._shared_queue.empty():
                    job_class, job_kwargs, priority = self._shared_queue.get_nowait()
                    if job_class is not None:
                        _add_job(job_class, job_kwargs, priority)
                    else:
                        _cancel_job(**job_kwargs)

        def _add_job(job_class, job_kwargs, priority):
            nonlocal job_id
            next_job = job_class(id=job_id,
                                 config=self.config,
                                 db=self.db,
                                 listener=self.listener,
                                 **job_kwargs)
            job_id += 1

            if priority:
                next_job.cost = 0

            {
                FuzzJob:
                lambda: self.listener.new_fuzz_job(ident=next_job.id,
                                                   fuzzer=next_job.fuzzer_name,
                                                   sut=next_job.sut_name,
                                                   cost=next_job.cost,
                                                   batch=next_job.batch),
                ValidateJob:
                lambda: self.listener.new_validate_job(ident=next_job.id,
                                                       sut=next_job.sut_name,
                                                       issue_id=next_job.issue['id']), # NOTE: listener not notified about validate job cost
                ReduceJob:
                lambda: self.listener.new_reduce_job(ident=next_job.id,
                                                     sut=next_job.sut_name,
                                                     cost=next_job.cost,
                                                     issue_id=next_job.issue['id'],
                                                     size=len(next_job.issue['test'])),
                UpdateJob:
                lambda: self.listener.new_update_job(ident=next_job.id,
                                                     sut=next_job.sut_name), # NOTE: listener not notified about update job cost
            }[job_class]()

            job_queue.insert(0 if priority else len(job_queue), next_job)

        def _cancel_job(ident):
            if ident in running_jobs:
                Controller.kill_process_tree(running_jobs[ident]['proc'].pid)
            else:
                ident_idx = [job_idx for job_idx, job in enumerate(job_queue) if job.id == ident]
                if ident_idx:
                    self.listener.remove_job(ident=ident)
                    del job_queue[ident_idx[0]]

        try:
            while True:
                # Update load and poll added jobs (if any).
                _poll_jobs()
                _update_load()

                if fuzz_idx == 0:
                    cycle += 1
                if cycle > max_cycles or (not self.fuzzers and max_cycles != float('inf')):
                    while load > 0:
                        time.sleep(1)
                        _poll_jobs() # only to let running jobs cancelled; newly added jobs don't get scheduled
                        _update_load()
                    break

                # Hunt for new issues only if there is no other work to do.
                if not job_queue:
                    if not self.fuzzers:
                        time.sleep(1)
                        continue

                    # Determine fuzz job to be queued and then update fuzz_idx
                    # to point to the next job's parameters.
                    fuzzer_name = self.fuzzers[fuzz_idx]
                    fuzz_section = 'fuzz.' + fuzzer_name
                    fuzz_idx = (fuzz_idx + 1) % len(self.fuzzers)

                    # Skip fuzz job if limit on parallel instances is reached.
                    instances = self.config.get(fuzz_section, 'instances', fallback='inf')
                    instances = float(instances) if instances == 'inf' else int(instances)
                    if instances <= sum(1 for job in running_jobs.values() if isinstance(job['job'], FuzzJob) and job['job'].fuzzer_name == fuzzer_name):
                        continue

                    # Before queueing a new fuzz job, check if we are working
                    # with the latest version of the SUT and queue an update if
                    # needed.
                    sut_name = self.config.get(fuzz_section, 'sut')
                    update_condition, update_condition_kwargs = config_get_callable(self.config, 'sut.' + sut_name, 'update_condition')
                    if update_condition:
                        with update_condition:
                            if update_condition(**update_condition_kwargs):
                                self.add_update_job(sut_name)

                    self.add_fuzz_job(fuzzer_name)

                    # Poll newly added job(s). Looping ensures that jobs will
                    # eventually arrive.
                    # (Unfortunately, multiprocessing.Queue.empty() is unreliable.)
                    while not job_queue:
                        _poll_jobs()

                # Perform next job as soon as there is enough capacity for it.
                while True:
                    if not job_queue:
                        next_job = None
                        break
                    elif load + job_queue[0].cost <= self.capacity:
                        next_job = job_queue.pop(0)
                        break
                    time.sleep(1)
                    _poll_jobs()
                    _update_load()
                if not next_job:
                    continue

                proc = Process(target=self._run_job, args=(next_job,))
                running_jobs[next_job.id] = dict(job=next_job, proc=proc)
                self.listener.activate_job(ident=next_job.id)
                proc.start()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.listener.warning(msg='Exception in the main controller loop: {exception}\n{trace}'.format(exception=e, trace=traceback.format_exc()))
        finally:
            Controller.kill_process_tree(os.getpid(), kill_root=False)
            if os.path.exists(self.work_dir):
                shutil.rmtree(self.work_dir, ignore_errors=True)

    def _run_job(self, job):
        try:
            for issue in job.run():
                # Automatic reduction and/or validation if the job found something new
                self.add_reduce_job(issue=issue) or self.add_validate_job(issue=issue)
        except Exception as e:
            self.listener.warning(msg='Exception in {job}: {exception}\n{trace}'.format(
                job=repr(job),
                exception=e,
                trace=traceback.format_exc()))

    def add_fuzz_job(self, fuzzer_name, priority=False):
        # Added for the sake of completeness and consistency.
        # Should not be used by UI to add fuzz jobs.
        with self._shared_lock:
            self._shared_queue.put((FuzzJob, dict(fuzzer_name=fuzzer_name), priority))
        return True

    def add_validate_job(self, issue, priority=False):
        with self._shared_lock:
            self._shared_queue.put((ValidateJob, dict(issue=issue), priority))
        return True

    def add_reduce_job(self, issue, priority=False):
        if not self.config.has_option('sut.' + issue['sut'], 'reduce'):
            return False

        with self._shared_lock:
            self._shared_queue.put((ReduceJob, dict(issue=issue), priority))
        return True

    def add_update_job(self, sut_name, priority=False):
        if not self.config.has_option('sut.' + sut_name, 'update'):
            return False

        with self._shared_lock:
            self._shared_queue.put((UpdateJob, dict(sut_name=sut_name), priority))
        return True

    def reduce_all(self):
        for issue in self.db.find_issues_by_suts([section for section in self.config.sections() if section.startswith('sut.') and section.count('.') == 1]):
            if not issue['reported'] and not issue['reduced']:
                self.add_reduce_job(issue)

    def cancel_job(self, ident):
        with self._shared_lock:
            self._shared_queue.put((None, dict(ident=ident), None))
        return True

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
