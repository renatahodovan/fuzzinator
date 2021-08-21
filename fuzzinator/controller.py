# Copyright (c) 2016-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import shutil
import time
import traceback

from math import inf
from multiprocessing import Lock, Process, Queue

import psutil

from .config import as_bool, as_int_or_inf, as_path, config_get_fuzzers, config_get_kwargs, config_get_object
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
          ``~/.fuzzinator/{uid}``)

        - Option ``db_uri``: URI to a MongoDB database to store found issues and
          execution statistics. (Optional, default:
          ``mongodb://localhost/fuzzinator``)

        - Option ``db_server_selection_timeout``: Controls how long the database
          driver will wait to find an available server (in milliseconds).
          (Optional, default: 30000)

        - Option ``cost_budget``: (Optional, default: number of cpus)

        - Option ``validate_after_update``: Boolean to enable the validation
          of valid issues of all SUTs after their update.
          (Optional, default: ``False``)

      - Sections ``sut.NAME``: Definitions of a SUT named *NAME*

        - Option ``call``: Fully qualified name of a callable context manager
          class. When an instance of the class is called, it must accept a
          ``test`` keyword argument representing the input to the SUT and must
          return a dictionary object if the input triggered an issue in the SUT,
          or a value considered false otherwise (which can be a simple ``None``,
          but can also be a ``NonIssue`` in complex cases). The returned issue
          dictionary (if any) *should* contain an ``'id'`` field that equals for
          issues that are not considered unique. (Mandatory)

          See package :mod:`fuzzinator.call` for potential SUT calls.

        - Option ``cost``: (Optional, default: 1)

        - Option ``validate_call``: Fully qualified name of a callable context
          manager class that acts as the SUT's ``call`` option during test case
          validation. (Optional, default: the value of option ``call``)

          See package :mod:`fuzzinator.call` for potential SUT calls.

        - Option ``validate_cost``: (Optional, default: the value of option
          ``cost``)

        - Option ``reduce``: Fully qualified name of a callable class. When an
          instance of the class is called, it must accept ``issue``,
          ``sut_call``, ``on_job_progressed`` keyword arguments representing
          an issue to be reduced, and must return a tuple consisting of a
          reduced test case for the issue (or ``None`` if the issue's current
          test case could not be reduced) and a (potentially empty) list of new
          issues that were discovered during test case reduction (if any).
          (Optional, no reduction for this SUT if option is missing.)

          See package :mod:`fuzzinator.reduce` for potential reducers.

        - Option ``reduce_call``: Fully qualified name of a callable context
          manager class that acts as the SUT's ``call`` option during test case
          reduction. (Optional, default: the value of option ``validate_call``
          if defined, otherwise the value of option ``call``)

          See package :mod:`fuzzinator.call` for potential SUT calls.

        - Option ``reduce_cost``: (Optional, default: the value of option
          ``cost``)

        - Option ``update_condition``: Fully qualified name of a callable class.
          When an instance of the class is called, it must return ``True`` if
          and only if the SUT should be updated. (Optional, SUT is never updated
          automatically if option is missing.)

          See package :mod:`fuzzinator.update` for potential update conditions.

        - Option ``update``: Fully qualified name of a callable class. When an
          instance of the class is called, it should perform the update of the
          SUT. (Optional, SUT is never updated if option is missing.)

          See package :mod:`fuzzinator.update` for potential updaters.

        - Option ``update_cost``: (Optional, default: the value of option
          ``fuzzinator:cost_budget``)

        - Option ``validate_after_update``: Boolean to enable the validation
          of the valid issues of the SUT after its update. (Optional, default:
          the value of option ``fuzzinator:validate_after_update``)

        - Option ``formatter``: Fully qualified name of a callable class. When
          an instance of the class is called, it must format the issue
          dictionary of the SUT by returning a custom string representation. It
          must accept an ``issue`` keyword argument representing an issue to be
          formatted. The class must also contain a method named ``summary``,
          also accepting an ``issue`` keyword argument, which should return a
          summary description (preferably a single line of text). (Optional,
          default: :func:`fuzzinator.formatter.JsonFormatter`.)

          See package :mod:`fuzzinator.formatter` for further potential
          formatters.

        - Options ``tui_formatter``, ``wui_formatter``, and ``email_formatter``:
          Fully qualified name of a callable class that formats the issue
          dictionary of the SUT to display it in the TUI issue viewer, on the
          WUI issue page, or to insert it into an e-mail notification.
          (Optional, default: the value of option ``formatter``)

          See package :mod:`fuzzinator.formatter` for potential formatters.

        - Option ``exporter``: Fully qualified name of a callable class. When an
          instance of the class is called, it must export the issue dictionary
          in a custom SUT-specific format. It must accept an ``issue`` keyword
          argument representing the issue to be exported and its result must be
          writable to a file, i.e., it must be either a string or a byte array.
          The export format does not necessarily have to contain all elements of
          the issue dictionary (e.g., it is often useful to only extract the
          test input that triggered the issue). (Optional, no custom export for
          this SUT if option is missing.)

          See package :mod:`fuzzinator.exporter` for potential exporters.

        - Option ``tracker``: Fully qualified name of a class that can report
          issues to an external issue tracker. (Optional, no reporting to
          tracker if option is missing.)

          See package :mod:`fuzzinator.tracker` for potential trackers.

      - Sections ``fuzz.NAME``: Definitions of a fuzz job named *NAME*

        - Option ``sut``: Name of the SUT that describes the subject of
          this fuzz job. (Mandatory)

        - Option ``fuzzer``: Fully qualified name of a callable context manager
          class. When an instance of the class is called, it must accept an
          ``index`` keyword argument representing a running counter in the fuzz
          job and must return a test input (or ``None``, which signals that the
          fuzzer is "exhausted" and cannot generate more test cases in this fuzz
          job). The semantics of the generated test input is not restricted by
          the framework, it is up to the configuration to ensure that the SUT of
          the fuzz job can deal with the tests generated by the fuzzer of the
          fuzz job. (Mandatory)

          See package :mod:`fuzzinator.fuzzer` for potential fuzzers.

        - Option ``batch``: Number of times the fuzzer is requested to generate
          a new test for the SUT. (Optional, default: 1)

        - Option ``instances``: Number of instances of this fuzz job allowed to
          run in parallel. (Optional, default: ``inf``)

        - Option ``refresh``: Statistics update frequency in terms of executed
          test cases. (Optional, default: ``batch`` size)

      - Section ``listeners``: Definitions of custom event listeners.
        This section is optional.

        - Options ``OPT``: Fully qualified name of a class that executes custom
          actions for selected events.

        See package :mod:`fuzzinator.listener` for potential listeners.

      - For classes referenced in options with their fully qualified name,
        constructor keyword arguments can be given. These arguments have to be
        specified in sections ``(sut|fuzz).NAME.OPT`` with appropriate names.

      - All classes can be decorated according to python semantics. The
        decorators must be callable classes and have to be specified in options
        ``OPT.decorate(N)`` with fully qualified name. Multiple decorators can
        be applied to a class ``OPT``, their order is specified by an integer
        index in parentheses. Keyword arguments to be passed to the decorators
        have to be listed in sections ``(sut|fuzz).NAME.OPT.decorate(N)``.

        See packages :mod:`fuzzinator.call` and :mod:`fuzzinator.fuzzer` for
        potential decorators.

      - The constructors of all classes (including decorators) can have a
        ``work_dir`` keyword argument. If present, its value is not filled in
        from the corresponding section but provided by the framework with a
        unique path under ``fuzzinator:work_dir``.
    """

    def __init__(self, config):
        """
        :param ~configparser.ConfigParser config: the configuration options of
            the fuzz session.

        :ivar ListenerManager listener: a listener manager object that is called
            on various events during the fuzz session.
        """
        self.config = config

        work_dir = self.config.get('fuzzinator', 'work_dir').format(uid=os.getpid())
        self.config.set('fuzzinator', 'work_dir', work_dir.replace('$', '$$'))
        self.work_dir = as_path(work_dir)
        self.fuzzers = config_get_fuzzers(self.config)

        self.capacity = int(self.config.get('fuzzinator', 'cost_budget'))
        self.validate_after_update = as_bool(self.config.get('fuzzinator', 'validate_after_update'))

        self.db = MongoDriver(self.config.get('fuzzinator', 'db_uri'),
                              int(self.config.get('fuzzinator', 'db_server_selection_timeout')))
        self.db.init_db(self.fuzzers)

        self.session_start = time.time()
        self.session_baseline = self.db.get_stats()

        self.listener = ListenerManager()
        for name in config_get_kwargs(self.config, 'listeners'):
            self.listener += config_get_object(self.config, 'listeners', name, init_kwargs=dict(config=config))

        self._shared_queue = Queue()
        self._shared_lock = Lock()

    def run(self, *, max_cycles=None, validate=None, reduce=None):
        """
        Start the fuzz session.

        :param int max_cycles: maximum number to iterate through the fuzz jobs
            defined in the configuration (defaults to ``inf``).
        :param str validate: name of SUT to validate issues of at the start of
            the fuzz session (the empty string denotes all SUTs; defaults to no
            SUT).
        :param str reduce: name of SUT to reduce issues of at the start of the
            fuzz session (the empty string denotes all SUTs; defaults to no
            SUT).
        """
        max_cycles = max_cycles if max_cycles is not None else inf
        cycle = 0
        fuzz_idx = 0
        fuzz_names = list(self.fuzzers)
        load = 0
        job_id = 0
        job_queue = []
        running_jobs = {}

        def _update_load():
            current_load = 0
            for job_id in list(running_jobs):
                if not running_jobs[job_id]['proc'].is_alive() or not psutil.pid_exists(running_jobs[job_id]['proc'].pid):
                    self.listener.on_job_removed(job_id=job_id)
                    del running_jobs[job_id]
                else:
                    current_load += running_jobs[job_id]['job'].cost

            nonlocal load
            if load != current_load:
                load = current_load
                self.listener.on_load_updated(load=load)

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
                lambda: self.listener.on_fuzz_job_added(job_id=next_job.id,
                                                        cost=next_job.cost,
                                                        sut=next_job.sut_name,
                                                        fuzzer=next_job.fuzzer_name,
                                                        batch=next_job.batch),
                ValidateJob:
                lambda: self.listener.on_validate_job_added(job_id=next_job.id,
                                                            cost=next_job.cost,
                                                            sut=next_job.sut_name,
                                                            issue_oid=next_job.issue['_id'],
                                                            issue_id=next_job.issue['id']),
                ReduceJob:
                lambda: self.listener.on_reduce_job_added(job_id=next_job.id,
                                                          cost=next_job.cost,
                                                          sut=next_job.sut_name,
                                                          issue_oid=next_job.issue['_id'],
                                                          issue_id=next_job.issue['id'],
                                                          size=len(str(next_job.issue['test']))),
                UpdateJob:
                lambda: self.listener.on_update_job_added(job_id=next_job.id,
                                                          cost=next_job.cost,
                                                          sut=next_job.sut_name),
            }[job_class]()

            job_queue.insert(0 if priority else len(job_queue), next_job)

        def _cancel_job(job_id):
            if job_id in running_jobs:
                Controller.kill_process_tree(running_jobs[job_id]['proc'].pid)
            else:
                job_idx = [job_idx for job_idx, job in enumerate(job_queue) if job.id == job_id]
                if job_idx:
                    self.listener.on_job_removed(job_id=job_id)
                    del job_queue[job_idx[0]]

        if validate is not None:
            self.validate_all(sut_name=validate)
        if reduce is not None:
            self.reduce_all(sut_name=reduce)

        try:
            while True:
                # Update load and poll added jobs (if any).
                _poll_jobs()
                _update_load()

                if fuzz_idx == 0:
                    cycle += 1
                if cycle > max_cycles or (not self.fuzzers and max_cycles != inf):
                    while load > 0:
                        time.sleep(1)
                        _poll_jobs()  # only to let running jobs cancelled; newly added jobs don't get scheduled
                        _update_load()
                    break

                # Hunt for new issues only if there is no other work to do.
                if not job_queue:
                    if not self.fuzzers:
                        time.sleep(1)
                        continue

                    # Determine fuzz job to be queued and then update fuzz_idx
                    # to point to the next job's parameters.
                    fuzzer_name = fuzz_names[fuzz_idx]
                    fuzz_section = 'fuzz.' + fuzzer_name
                    fuzz_idx = (fuzz_idx + 1) % len(self.fuzzers)

                    # Skip fuzz job if limit on parallel instances is reached.
                    instances = as_int_or_inf(self.config.get(fuzz_section, 'instances', fallback='inf'))
                    if instances <= sum(1 for job in running_jobs.values() if isinstance(job['job'], FuzzJob) and job['job'].fuzzer_name == fuzzer_name):
                        continue

                    # Before queueing a new fuzz job, check if we are working
                    # with the latest version of the SUT and queue an update if
                    # needed.
                    sut_name = self.config.get(fuzz_section, 'sut')
                    update_condition = config_get_object(self.config, 'sut.' + sut_name, 'update_condition')
                    if update_condition and update_condition():
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
                    if load + job_queue[0].cost <= self.capacity:
                        next_job = job_queue.pop(0)
                        break
                    time.sleep(1)
                    _poll_jobs()
                    _update_load()
                if not next_job:
                    continue

                proc = Process(target=self._run_job, args=(next_job,))
                running_jobs[next_job.id] = dict(job=next_job, proc=proc)
                self.listener.on_job_activated(job_id=next_job.id)
                proc.start()

        except KeyboardInterrupt:
            pass
        except Exception as e:
            self.listener.warning(job_id=None, msg='Exception in the main controller loop: {exception}\n{trace}'.format(exception=e, trace=traceback.format_exc()))
        finally:
            Controller.kill_process_tree(os.getpid(), kill_root=False)
            if os.path.exists(self.work_dir):
                shutil.rmtree(self.work_dir, ignore_errors=True)

    def _run_job(self, job):
        try:
            for issue in job.run():
                # Automatic reduction and/or validation if the job found something new
                if not self.add_reduce_job(issue=issue):
                    self.add_validate_job(issue=issue)
        except Exception as e:
            self.listener.warning(job_id=job.id, msg='Exception in {job}: {exception}\n{trace}'.format(
                job=repr(job),
                exception=e,
                trace=traceback.format_exc()))

    def add_fuzz_job(self, fuzzer_name, priority=False):
        # Added for the sake of completeness and consistency.
        # Should not be used by UI to add fuzz jobs.
        with self._shared_lock:
            self._shared_queue.put((FuzzJob, dict(fuzzer_name=fuzzer_name, subconfig_id=self.fuzzers[fuzzer_name]['subconfig']), priority))
        return True

    def add_validate_job(self, issue, priority=False):
        if not self.config.has_section('sut.' + issue['sut']):
            return False

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

        if as_bool(self.config.get('sut.' + sut_name, 'validate_after_update', fallback=self.validate_after_update)):
            self.validate_all(sut_name)

        return True

    def validate_all(self, sut_name=None):
        sut_name = [sut_name] if sut_name else [section.split('.', maxsplit=1)[1] for section in self.config.sections() if section.startswith('sut.') and section.count('.') == 1]
        for issue in self.db.find_issues_by_suts(sut_name):
            if not issue.get('invalid'):
                self.add_validate_job(issue)

    def reduce_all(self, sut_name=None):
        sut_name = [sut_name] if sut_name else [section.split('.', maxsplit=1)[1] for section in self.config.sections() if section.startswith('sut.') and section.count('.') == 1]
        for issue in self.db.find_issues_by_suts(sut_name):
            if not issue.get('reported') and not issue.get('reduced') and not issue.get('invalid'):
                self.add_reduce_job(issue)

    def cancel_job(self, job_id):
        with self._shared_lock:
            self._shared_queue.put((None, dict(job_id=job_id), None))
        return True

    @staticmethod
    def kill_process_tree(pid, kill_root=True):
        try:
            root_proc = psutil.Process(pid)
            children = root_proc.children(recursive=True)
            if kill_root:
                children.append(root_proc)
            for proc in children:
                try:
                    proc.terminate()
                except psutil.Error:
                    pass
            _, alive = psutil.wait_procs(children, timeout=1)
            for proc in alive:
                try:
                    proc.kill()
                except psutil.Error:
                    pass
        except psutil.NoSuchProcess:
            pass
