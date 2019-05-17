# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from email import message_from_string
from pkg_resources import get_distribution


dist = get_distribution(__package__)
meta = message_from_string(dist.get_metadata(dist.PKG_INFO))

__pkg_name__ = dist.project_name
__version__ = dist.version
__author__ = meta['Author']
__author_email__ = meta['Author-email']
__url__ = meta['Home-page']
