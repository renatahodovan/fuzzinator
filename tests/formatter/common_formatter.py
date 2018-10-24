# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from os.path import abspath, dirname, join


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


def mock_id_formatter(issue, format='long', **kwargs):
    """
    Always return the issue id converted to its string representation.
    """
    return str(issue['id'])


class MockFixedFormatter(object):
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
