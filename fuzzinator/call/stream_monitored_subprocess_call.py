# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import errno
import fcntl
import json
import logging
import os
import re
import shlex
import select
import signal
import subprocess
import sys
import time

from fuzzinator import Controller

logger = logging.getLogger(__name__)


class StreamMonitoredSubprocessCall(object):
    """
    .. note::

       Not available on platforms without fcntl support (e.g., Windows).
    """

    def __init__(self, command, cwd=None, env=None, end_patterns=None, timeout=None, **kwargs):
        self.command = command
        self.cwd = cwd or os.getcwd()
        self.end_patterns = [re.compile(pattern.encode('utf-8', errors='ignore'), flags=re.MULTILINE | re.DOTALL) for pattern in json.loads(end_patterns)] if end_patterns else []
        self.env = dict(os.environ, **json.loads(env)) if env else None
        self.timeout = int(timeout) if timeout else None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def __call__(self, test, **kwargs):
        if self.timeout:
            start_time = time.time()

        proc = subprocess.Popen(shlex.split(self.command.format(test=test), posix=sys.platform != 'win32'),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                cwd=self.cwd or os.getcwd(),
                                env=self.env)

        streams = {'stdout': b'', 'stderr': b''}
        issue = None

        select_fds = [stream.fileno() for stream in [proc.stderr, proc.stdout]]
        for fd in select_fds:
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        end_loop = False
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

                        for pattern in self.end_patterns:
                            match = pattern.search(streams[stream])
                            if match is not None:
                                end_loop = True
                                issue = match.groupdict()

                if proc.poll() is not None or (self.timeout and time.time() - start_time > self.timeout):
                    break
            except IOError as e:
                logger.warning('[filter_streams] %s' % str(e))

        Controller.kill_process_tree(proc.pid, sig=signal.SIGKILL)

        logger.debug('{stdout}\n{stderr}'.format(stdout=streams['stdout'].decode('utf-8', errors='ignore'),
                                                 stderr=streams['stderr'].decode('utf-8', errors='ignore')))
        if issue:
            issue.update(dict(exit_code=proc.returncode,
                              stderr=streams['stderr'],
                              stdout=streams['stdout']))
        return issue
