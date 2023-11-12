# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import sys

import pytest

import fuzzinator

from .common_update import resources_dir


@pytest.mark.parametrize('command, cwd, env', [
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args foo ', None, None),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-args --to-stderr --exit-code 1 foo', None, None),
    (f'{sys.executable} {os.path.join(resources_dir, "mock_tool.py")} --print-env FOO', resources_dir, '{"FOO": "baz"}'),
])
def test_subprocess_update(command, cwd, env):
    fuzzinator.update.SubprocessUpdate(command=command, cwd=cwd, env=env)()
