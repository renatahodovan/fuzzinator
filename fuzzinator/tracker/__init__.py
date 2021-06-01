# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from .base import BaseTracker, TrackerError
from .bugzilla import BugzillaTracker
from .github import GithubTracker
from .gitlab import GitlabTracker
from .monorail import MonorailTracker
