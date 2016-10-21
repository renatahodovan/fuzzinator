# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json

from string import Template

from fuzzinator.config import config_get_callable


class SingletonMetaClass(type):

    def __init__(cls, name, bases, dict):
        _instances = {}

        def __call__(cls, *args, **kwargs):
            if cls not in cls._instances:
                cls._instances[cls] = super(SingletonMetaClass, cls).__call__(*args, **kwargs)
            return cls._instances[cls]


class BaseTracker(object, metaclass=SingletonMetaClass):

    db = None

    def __init__(self, template=None, title=None):
        self.template = template
        self.title_fmt = title

    @property
    def logged_in(self):
        return True

    def title(self, issue):
        return self.title_fmt.format(**self.decode_issue(issue)) if self.title_fmt else issue['id']

    def decode_issue(self, issue):
        def universal_newlines(src):
            if type(src) == str:
                return '\n'.join(src.splitlines())
            return src
        return dict((x, universal_newlines(y.decode('utf-8', errors='ignore')) if type(y) == bytes else universal_newlines(y)) for (x, y) in issue.items() if x != '_id')

    def format_issue(self, issue):
        if self.template:
            with open(self.template, 'r') as f:
                return Template(f.read()).substitute(self.decode_issue(issue))
        return json.dumps(self.decode_issue(issue), indent=4, sort_keys=True)

    def find_issue(self, issue):
        pass

    def report_issue(self, **kwargs):
        pass

    def set_reported(self, issue, url):
        self.db.update_issue(issue, {'reported': url})


def init_tracker(config, sut_section, db):
    if config.has_option(sut_section, 'report'):
        tracker, _ = config_get_callable(config, sut_section, 'report')
    else:
        tracker = BaseTracker()

    tracker.db = db
    return tracker
