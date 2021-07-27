# Copyright (c) 2018-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from os.path import abspath, dirname, join

import fuzzinator


resources_dir = join(dirname(dirname(abspath(__file__))), 'resources')
mock_templates_dir = join(resources_dir, 'mock_templates')


mock_issue = {
    'id': 'foo',
    'bar': True,
    'baz': False,
    'qux': {
        'xyz': 42,
    },
}


class MockIdFormatter(fuzzinator.formatter.Formatter):
    """
    Always return the issue id converted to its string representation.
    """

    def __init__(self, **kwargs):
        pass

    def __call__(self, issue, format='long', **kwargs):
        return str(issue['id'])


class MockFixedFormatter(fuzzinator.formatter.Formatter):
    """
    Always return fixed strings for short and long variants.
    """

    def __init__(self, short, long, **kwargs):
        self.strings = {
            'short': short,
            'long': long,
        }

    def __call__(self, issue, format='long', **kwargs):
        return self.strings[format]
