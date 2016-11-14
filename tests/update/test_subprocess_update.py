# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import pytest
import os

import fuzzinator

from common_update import resources_dir


@pytest.mark.parametrize('command, cwd, env', [
    ('%s --print-args foo ' % os.path.join(resources_dir, 'mock_tool.py'), None, None),
    ('%s --print-args --to-stderr --exit-code 1 foo' % os.path.join(resources_dir, 'mock_tool.py'), None, None),
    ('%s --print-env FOO' % os.path.join('.', 'mock_tool.py'), resources_dir, '{"FOO": "baz"}'),
])
def test_subprocess_update(command, cwd, env):
    fuzzinator.update.SubprocessUpdate(command, cwd=cwd, env=env)
