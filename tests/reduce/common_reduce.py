# Copyright (c) 2018 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from os.path import abspath, dirname, join


resources_dir = join(dirname(dirname(abspath(__file__))), 'resources')
mock_grammars_dir = join(resources_dir, 'mock_grammars')


class MockFailIfContainsCall(object):
    """
    Return an issue dictionary if ``test`` contains one of the specified
    ``strings``. The ``id`` of the returned issue is the found string. Return
    ``None`` if no string is found.
    """

    def __init__(self, strings):
        self.strings = strings

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return None

    def __call__(self, test, *args, **kwargs):
        for s in self.strings:
            if s in test:
                return {'id': s, 'test': test}
        return None
