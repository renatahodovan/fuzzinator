# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from .callable_decorator import CallableDecorator
from .anonymize_decorator import AnonymizeDecorator
from .exit_code_filter import ExitCodeFilter
from .file_reader_decorator import FileReaderDecorator
from .file_writer_decorator import FileWriterDecorator
from .gdb_backtrace_decorator import GdbBacktraceDecorator
from .lldb_backtrace_decorator import LldbBacktraceDecorator
from .platform_info_decorator import PlatformInfoDecorator
from .regex_filter import RegexFilter
from .stdin_subprocess_call import StdinSubprocessCall
from .subprocess_call import SubprocessCall
from .subprocess_property_decorator import SubprocessPropertyDecorator
from .unique_id_decorator import UniqueIdDecorator

__all__ = [
    'AnonymizeDecorator',
    'CallableDecorator',
    'ExitCodeFilter',
    'FileReaderDecorator',
    'FileWriterDecorator',
    'GdbBacktraceDecorator',
    'LldbBacktraceDecorator',
    'PlatformInfoDecorator',
    'RegexFilter',
    'StdinSubprocessCall',
    'SubprocessCall',
    'SubprocessPropertyDecorator',
    'UniqueIdDecorator',
]

try:
    from .stream_monitored_subprocess_call import StreamMonitoredSubprocessCall
    __all__.append('StreamMonitoredSubprocessCall')
except ImportError:
    pass

try:
    from .test_runner_subprocess_call import TestRunnerSubprocessCall
    __all__.append('TestRunnerSubprocessCall')
except ImportError:
    pass

# sorting __all__ has no functional use but seems to be needed to get
# autodoc-generated sections in the correct alphabetical order
# (autodoc_member_order='alphabetical' in docs/conf.py didn't do the job)
__all__.sort()
