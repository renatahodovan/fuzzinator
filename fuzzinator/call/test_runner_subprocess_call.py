# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import errno
import fcntl
import json
import logging
import os
import select
import shlex
import subprocess

logger = logging.getLogger(__name__)


class TestRunnerSubprocessCall(object):

    def __init__(self, command, cwd=None, env=None, end_texts=None, init_wait=None, **kwargs):
        self.end_texts = json.loads(end_texts) if end_texts else []
        self.init_wait = eval(init_wait) if init_wait else False
        self.cwd = cwd or os.getcwd()
        self.command = command
        self.env = dict(os.environ, **json.loads(env)) if env else None
        self.proc = None

    def __enter__(self):
        self.start(self.init_wait)
        return self

    def __exit__(self, *exc):
        return None

    def __call__(self, test, **kwargs):
        if not self.proc or self.proc.poll():
            self.start(self.init_wait)

        try:
            self.proc.stdin.write((test + '\n').encode('utf-8'))
            self.proc.stdin.flush()
            issue = self.wait_til_end()
            return issue
        except:
            return None

    def start(self, init_wait=True):
        self.proc = subprocess.Popen(shlex.split(self.command),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     stdin=subprocess.PIPE,
                                     close_fds=True,
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
        while not end_loop:
            try:
                try:
                    read_fds = select.select(select_fds, [], select_fds, 0.5)[0]
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

                if self.proc.poll() is not None:
                    break
            except IOError as e:
                logger.warn('[filter_streams] %s' % str(e))

        return {
            'exit_code': self.proc.returncode,
            'stderr': streams['stderr'],
            'stdout': streams['stdout'],
        }
