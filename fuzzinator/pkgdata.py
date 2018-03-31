# Copyright (c) 2016-2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import pkgutil


data = json.loads(pkgutil.get_data(__package__, 'PKGDATA.json').decode('ascii'))
__pkg_name__ = data['name']
__version__ = data['version']
__author__ = data['author']
__author_email__ = data['author_email']
__url__ = data['url']
