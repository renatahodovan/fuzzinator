# Copyright (c) 2016-2019 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from urwid import *

from ...config import config_get_callable
from ...formatter import JsonFormatter
from ...tracker import BaseTracker, BugzillaTracker
from .button import FormattedButton
from .decor_widgets import PatternBox
from .dialogs import BugEditor
from .graphics import fz_box_pattern


class ReportDialog(PopUpTarget):
    signals = ['close']

    def __init__(self, issue, config, db, side_bar=None):
        self.issue = issue
        self.tracker = config_get_callable(config, 'sut.' + issue['sut'], 'tracker')[0] or BaseTracker()
        self.db = db
        self.duplicate = None

        self.edit_dups = BugEditor()
        self.result = Text('')
        formatter = config_get_callable(config, 'sut.' + issue['sut'], 'formatter')[0] or JsonFormatter
        self.issue_title = BugEditor(edit_text=formatter(issue=issue, format='short'))
        self.issue_desc = BugEditor(edit_text=formatter(issue=issue), multiline=True, wrap='clip')
        self.body = SimpleListWalker([Columns([('fixed', 13, Text(('dialog_secondary', 'Summary: '))),
                                               ('weight', 10, self.issue_title)], dividechars=1),
                                      Columns([('fixed', 13, Text(('dialog_secondary', 'Description: '))),
                                               ('weight', 10, self.issue_desc)], dividechars=1)])
        frame = Frame(body=AttrMap(Columns([('weight', 10, ListBox(self.body)),
                                            ('weight', 3, AttrMap(ListBox(SimpleListWalker(side_bar or [])), attr_map='dialog_secondary'))]),
                                   'dialog'),
                      footer=Columns([('pack', FormattedButton('Close', lambda button: self._emit('close_reporter'))),
                                      ('pack', FormattedButton('Report', lambda button: self.send_report())),
                                      ('pack', FormattedButton('Save as reported', lambda button: self.save_reported()))], dividechars=2),
                      focus_part='body')

        super().__init__(AttrMap(PatternBox(frame, title=('dialog_title', issue['id']), **fz_box_pattern()), attr_map='dialog_border'))
        self.find_duplicates()

    def set_duplicate(self, btn, state):
        if state:
            self.duplicate = btn.label

    def find_duplicates(self):
        dups_walker = SimpleListWalker([self.edit_dups])
        options = []
        for entry in self.tracker.find_issue(self.issue_title.get_text()[0]):
            radio_btn = RadioButton(options, self.tracker.issue_url(entry), on_state_change=self.set_duplicate)
            # Select the first suggested bug if there is not set any.
            if self.duplicate is None:
                self.duplicate = radio_btn.label
            dups_walker.append(radio_btn)
        self.body.insert(0, Columns([('fixed', 13, Text(('dialog_secondary', 'Duplicates: '))),
                                     ('weight', 10, BoxAdapter(ListBox(dups_walker), height=len(dups_walker)))]))

    def get_report_data(self):
        assert False, 'Should never be reached.'
        return dict()

    def send_report(self):
        url = self.tracker.issue_url(self.tracker.report_issue(**self.get_report_data()))
        self.result.set_text(('dialog_secondary', 'Reported at: {weburl}'.format(weburl=url)))
        self.db.update_issue_by_id(self.issue['_id'], {'reported': url})
        return url

    def save_reported(self):
        if self.edit_dups.text:
            url = self.edit_dups.text
        elif self.duplicate:
            url = self.duplicate
        else:
            url = ''
        self.db.update_issue_by_id(self.issue['_id'], {'reported': url})
        self._emit('close')

    def keypress(self, size, key):
        if key in ['esc', 'f7']:
            self._emit('close')
            return None
        return super().keypress(size, key)


class BugzillaReportDialog(ReportDialog):

    def __init__(self, issue, config, db):
        self.edit_blocks = BugEditor()
        self.edit_cc = BugEditor(multiline=True)
        self.edit_extension = BugEditor(edit_text='html')

        tracker = config_get_callable(config, 'sut.' + issue['sut'], 'tracker')[0]
        assert isinstance(tracker, BugzillaTracker), 'Tracker is not a Bugzilla instance.'
        self.product_info = tracker.product_info()
        self.product = None
        products_walker = SimpleListWalker([])
        products = []
        for product in self.product_info:
            products_walker.append(RadioButton(products, product, on_state_change=self.set_product))

        self.component = None
        self.component_box = SimpleFocusListWalker([])

        self.version = None
        self.versions_box = SimpleFocusListWalker([])

        side_bar = [LineBox(BoxAdapter(ListBox(products_walker), height=len(products_walker)), title='Products'),
                    LineBox(BoxAdapter(ListBox(self.component_box), height=10), title='Components'),
                    LineBox(BoxAdapter(ListBox(self.versions_box), height=10), title='Versions'),
                    Columns([('weight', 1, Text('CC: ')), ('weight', 4, self.edit_cc)]),
                    Columns([('weight', 1, Text('Blocks: ')), ('weight', 4, self.edit_blocks)]),
                    Columns([('weight', 1, Text('Ext: ')), ('weight', 4, self.edit_extension)])]

        super().__init__(issue=issue, config=config, db=db, side_bar=side_bar)
        self.set_product(products_walker.contents[0], True)

    def set_product(self, btn, state):
        if state:
            self.product = btn.label
            self.update_components(self.product_info[self.product]['components'])
            self.update_versions(self.product_info[self.product]['versions'])

    def set_component(self, btn, state):
        if state:
            self.component = btn.label

    def set_version(self, btn, state):
        if state:
            self.version = btn.label

    def update_components(self, components):
        components_group = []
        self.component_box.clear()
        for component in components:
            self.component_box.append(RadioButton(group=components_group, label=component, on_state_change=self.set_component))

    def update_versions(self, versions):
        versions_group = []
        self.versions_box.clear()
        for version in versions:
            self.versions_box.append(RadioButton(group=versions_group, label=version, on_state_change=self.set_version))

    def get_report_data(self):
        return dict(title=self.issue_title.edit_text,
                    body=self.issue_desc.edit_text,
                    product=self.product,
                    product_version=self.version,
                    component=self.component,
                    blocks=self.edit_blocks.edit_text,
                    test=self.issue['test'],
                    extension=self.edit_extension.edit_text)


class GithubReportDialog(ReportDialog):

    def get_report_data(self):
        return dict(title=self.issue_title.edit_text,
                    body=self.issue_desc.edit_text)


class MonorailReportDialog(ReportDialog):

    def get_report_data(self):
        return dict(title=self.issue_title.edit_text,
                    body=self.issue_desc.edit_text)


class GitlabReportDialog(ReportDialog):

    def get_report_data(self):
        return dict(title=self.issue_title.edit_text,
                    body=self.issue_desc.edit_text)
