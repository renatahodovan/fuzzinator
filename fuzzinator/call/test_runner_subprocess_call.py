# Copyright (c) 2016-2020 Renata Hodovan, Akos Kiss.
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
import subprocess
import time

from ..config import as_bool, as_dict, as_list, as_pargs, as_path
from .. import Controller

logger = logging.getLogger(__name__)


class TestRunnerSubprocessCall(object):
    """
    .. note::

       Not available on platforms without fcntl support (e.g., Windows).
    """

    def __init__(self, command, cwd=None, env=None, end_texts=None, init_wait=None, timeout_per_test=None, **kwargs):
        self.end_texts = as_list(end_texts) if end_texts else []
        self.init_wait = as_bool(init_wait)
        self.timeout_per_test = int(timeout_per_test) if timeout_per_test else None
        self.cwd = as_path(cwd) if cwd else os.getcwd()
        self.command = as_pargs(command)
        self.env = dict(os.environ, **as_dict(env)) if env else None
        self.proc = None

    def __enter__(self):
        self.start(self.init_wait)
        return self

    def __exit__(self, *exc):
        if self.proc and self.proc.poll() is None:
            Controller.kill_process_tree(self.proc.pid)
        return False

    def __call__(self, test, **kwargs):
        if not self.proc or self.proc.poll() is not None:
            self.start(self.init_wait)

        try:
            self.proc.stdin.write((test + '\n').encode('utf-8'))
            self.proc.stdin.flush()
            issue = self.wait_til_end()
            return issue
        except Exception:
            return None

    def start(self, init_wait=True):
        self.proc = subprocess.Popen(self.command,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     stdin=subprocess.PIPE,
                                     cwd=self.cwd,
                                     env=self.env)
        if init_wait:
            self.wait_til_end()

    def wait_til_end(self):
        streams = {'stdout': b'', 'stderr': b''}

        select_fds = [stream.fileno() for stream in [self.proc.stderr, self.proc.stdout]]
        for fd in select_fds:
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)

        end_loop = False
        start_time = time.time()
        while not end_loop:
            try:
                time_left = self.timeout_per_test - (time.time() - start_time) if self.timeout_per_test else 0.5
                if time_left <= 0:
                    # Avoid waiting for the current test in the next iteration.
                    Controller.kill_process_tree(self.proc.pid)
                    break

                try:
                    read_fds = select.select(select_fds, [], select_fds, time_left)[0]
                except select.error as e:
                    if e.args[0] == errno.EINVAL:
                        continue
                    raise

                for stream, _ in streams.items():
                    if getattr(self.proc, stream).fileno() in read_fds:
                        while True:
                            stdout_chunk = getattr(self.proc, stream).read(512)
                            if not stdout_chunk:
                                break
                            streams[stream] += stdout_chunk

                        for end_pattern in self.end_texts:
                            if end_pattern.encode('utf-8') in streams[stream]:
                                end_loop = True
                                break

                if self.proc.poll() is not None:
                    break
            except IOError as e:
                logger.warning('Exception in stream filtering.', exc_info=e)

        logger.debug('%s\n%s', streams['stdout'].decode('utf-8', errors='ignore'), streams['stderr'].decode('utf-8', errors='ignore'))
        return {
            'exit_code': self.proc.returncode,
            'stderr': streams['stderr'],
            'stdout': streams['stdout'],
        }
