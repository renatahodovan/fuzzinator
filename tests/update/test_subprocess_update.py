# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os
import pytest
import sys

import fuzzinator

from common_update import resources_dir


@pytest.mark.parametrize('command, cwd, env', [
    ('%s %s --print-args foo ' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None),
    ('%s %s --print-args --to-stderr --exit-code 1 foo' % (sys.executable, os.path.join(resources_dir, 'mock_tool.py')), None, None),
    ('%s %s --print-env FOO' % (sys.executable, os.path.join('.', 'mock_tool.py')), resources_dir, '{"FOO": "baz"}'),
])
def test_subprocess_update(command, cwd, env):
    fuzzinator.update.SubprocessUpdate(command, cwd=cwd, env=env)
