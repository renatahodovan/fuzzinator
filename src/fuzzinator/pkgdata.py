# Copyright (c) 2016-2024 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from importlib import metadata


dist = metadata.distribution(__package__)

__pkg_name__ = dist.metadata['Name']
__version__ = dist.version
__author__ = dist.metadata['Author']
__author_email__ = dist.metadata['Author-email']
__url__ = dist.metadata['Home-page']
