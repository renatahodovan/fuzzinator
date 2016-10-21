# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import errno
import fcntl
import json
import os
import re
import shlex
import select
import signal
import subprocess


class StreamMonitoredSubprocessCall(object):

    def __init__(self, command, cwd=None, env=None, end_patterns=None, **kwargs):
        self.command = command
        self.cwd = cwd or os.getcwd()
        self.end_patterns = [re.compile(pattern.encode('utf-8', errors='ignore')) for pattern in json.loads(end_patterns)] if end_patterns else []
        self.env = dict(os.environ, **json.loads(self.env)) if env else None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def __call__(self, test, **kwargs):
        self.proc = subprocess.Popen(shlex.split(self.command.format(test=test)),
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE,
                                     close_fds=True,
                                     cwd=self.cwd or os.getcwd(),
                                     env=self.env)
        return self.wait_til_end()

    def wait_til_end(self):
        streams = {'stdout': b'', 'stderr': b''}
        issue = None

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
                            chunk = getattr(self.proc, stream).read(512)
                            if not chunk:
                                break
                            streams[stream] += chunk

                        for pattern in self.end_patterns:
                            match = pattern.search(streams[stream])
                            if match is not None:
                                end_loop = True
                                issue = match.groupdict()

                        if self.proc.poll() is not None:
                            break

                if self.proc.poll() is not None:
                    break
            except IOError:
                pass

        try:
            os.kill(self.proc.pid, signal.SIGKILL)
        except:
            pass

        if issue:
            issue.update(dict(exit_code=self.proc.returncode,
                              stderr=streams['stderr'],
                              stdout=streams['stdout']))
        return issue
