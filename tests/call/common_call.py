# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import os


blinesep = os.linesep
resources_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'resources')


def mock_always_fail_call(**kwargs):
    """
    Unconditionally return an issue dictionary composed of all the keyword
    arguments of the function.
    """
    return dict(kwargs)


def mock_never_fail_call(**kwargs):
    """
    Unconditionally return ``None`` signaling no issue.
    """
    return None


class MockAlwaysFailCall(object):
    """
    Unconditionally return an issue dictionary composed of all the keyword
    arguments of the constructor and the call.
    """

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs

    def __call__(self, **kwargs):
        issue = dict(self.init_kwargs)
        issue.update(kwargs)
        return issue


class MockNeverFailCall(object):
    """
    Unconditionally return ``None`` signaling no issue.
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, **kwargs):
        return None
