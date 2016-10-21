# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import os
import subprocess

from .callable_decorator import CallableDecorator


class SubprocessPropertyDecorator(CallableDecorator):
    """
    Decorator for SUT calls to extend issues with an arbitrary property where
    the value is the output of a shell subprocess.

    Mandatory parameters of the decorator:
      - 'property': name of the property to extend the issue with.
      - 'command': string to pass to the child shell as a command to run.
    Optional parameters of the decorator:
      - 'cwd': if not None, change working directory before GDB/command
        invocation.
      - 'env': if not None, a dictionary of variable names-values to update the
        environment with.

    Example configuration snippet:
    [sut.foo]
    call=fuzzinator.call.StdinSubprocessCall
    call.decorate(0)=fuzzinator.call.SubprocessPropertyDecorator

    [sut.foo.call]
    command=./bin/foo -
    cwd=/home/alice/foo

    [sut.foo.call.decorate(0)]
    property=version
    command=git rev-parse --short HEAD
    cwd=${sut.foo.call:cwd}
    env={"GIT_FLUSH": "1"}
    """

    def decorator(self, property, command, cwd=None, env=None, **kwargs):
        def wrapper(fn):
            def filter(*args, **kwargs):
                issue = fn(*args, **kwargs)
                if not issue:
                    return None

                issue[property] = subprocess.check_output(command,
                                                          shell=True,
                                                          cwd=cwd or os.getcwd(),
                                                          env=dict(os.environ, **json.loads(env or '{}')))
                return issue

            return filter
        return wrapper
