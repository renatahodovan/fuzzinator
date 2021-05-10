# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import errno
import fcntl
import logging
import os
import select
import signal
import subprocess
import time

from ..config import as_dict, as_list, as_pargs, as_path
from .. import Controller
from . import RegexAutomaton

logger = logging.getLogger(__name__)


class StreamMonitoredSubprocessCall(object):
    """
    Subprocess invocation-based call of a SUT that takes test input on its
    command line. The main difference from
    :func:`fuzzinator.call.SubprocessCall` is that it continuously monitors
    the stdout and stderr streams of the SUT and forces it to terminate if
    some predefined patterns are appearing.

    **Mandatory parameter of the SUT call:**

      - ``command``: string to pass to the child shell as a command to run (all
        occurrences of ``{test}`` in the string are replaced by the actual test
        input).

    **Optional parameters of the SUT call:**

      - ``cwd``: if not ``None``, change working directory before the command
        invocation.
      - ``env``: if not ``None``, a dictionary of variable names-values to
        update the environment with.
      - ``end_patterns``: array of patterns to match against the lines of stdout
        and stderr streams. The patterns and instructions are interpreted as
        defined in :class:`fuzzinator.call.RegexAutomaton`.
      - ``timeout``: run subprocess with timeout.

    **Result of the SUT call:**

      - If processing stdout and stderr with ``end_patterns`` doesn't produce
        any result, no issue is returned.
      - Otherwise, an issue with keys from the matching patterns of
        ``end_pattern`` extended with the ``'exit_code'``, ``'stdout'``, and
        ``'stderr'`` properties is returned.

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            call=fuzzinator.call.StreamMonitoredSubprocessCall

            [sut.foo.call.init]
            # assuming that {test} is something that can be interpreted by foo as
            # command line argument
            command=./bin/foo {test}
            cwd=/home/alice/foo
            env={"BAR": "1"}
            end_patterns=["mss /(?P<file>[^:]+):(?P<line>[0-9]+): (?P<func>[^:]+): (?P<msg>Assertion `.*' failed)/"]
            timeout=30

    .. note::

       Not available on platforms without fcntl support (e.g., Windows).
    """

    def __init__(self, command, cwd=None, env=None, end_patterns=None, timeout=None, **kwargs):
        self.command = command
        self.cwd = as_path(cwd) if cwd else os.getcwd()
        self.end_patterns = [RegexAutomaton.split_pattern(p.encode('utf-8', errors='ignore')) for p in as_list(end_patterns)] if end_patterns else []
        self.env = dict(os.environ, **as_dict(env)) if env else None
        self.timeout = int(timeout) if timeout else None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def __call__(self, test, **kwargs):
        if self.timeout:
            start_time = time.time()

        proc = subprocess.Popen(as_pargs(self.command.format(test=test)),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=self.cwd or os.getcwd(),
                                env=self.env)

        streams = {'stdout': b'', 'stderr': b''}

        select_fds = [stream.fileno() for stream in [proc.stderr, proc.stdout]]
        for fd in select_fds:
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        issue = dict()
        end_loop = False
        regex_automaton = RegexAutomaton(self.end_patterns)
        while not end_loop:
            try:
                try:
                    read_fds = select.select(select_fds, [], select_fds, 0.5)[0]
                except select.error as e:
                    if e.args[0] == errno.EINVAL:
                        continue
                    raise

                for stream, _ in streams.items():
                    if getattr(proc, stream).fileno() in read_fds:
                        while True:
                            chunk = getattr(proc, stream).read(512)
                            if not chunk:
                                break
                            streams[stream] += chunk

                        # Process the stream content line-by-line.
                        terminate, new_details = regex_automaton.process(streams[stream].splitlines(), issue)
                        if new_details or terminate:
                            end_loop = True

                if proc.poll() is not None or (self.timeout and time.time() - start_time > self.timeout):
                    break
            except IOError as e:
                logger.warning('Exception in stream filtering.', exc_info=e)

        Controller.kill_process_tree(proc.pid, sig=signal.SIGKILL)

        logger.debug('%s\n%s', streams['stdout'].decode('utf-8', errors='ignore'), streams['stderr'].decode('utf-8', errors='ignore'))
        if issue:
            issue.update(dict(exit_code=proc.returncode,
                              stderr=streams['stderr'],
                              stdout=streams['stdout']))
            return issue
        return None
