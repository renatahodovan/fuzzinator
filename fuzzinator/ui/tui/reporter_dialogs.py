# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import json
import sys

from urwid import *
from .decor_widgets import PatternBox
from .graphics import fz_box_pattern


class BugzillaReportDialog(WidgetWrap):
    signals = ['close']

    def __init__(self, issue, tracker):
        self.issue = issue
        self.tracker = tracker

        # TODO: ugly! refactor needed!
        from .widgets import FormattedButton
        report_button = FormattedButton('Report', lambda button: self.report(btn=button))
        save_button = FormattedButton('Save as reported', lambda button: self.tracker.set_reported(self.issue, self.duplicate))
        close_button = FormattedButton('Close', lambda button: self._emit('close'))

        self.summary_box = Edit(caption='', edit_text=self.tracker.title(issue))
        self.desc_box = Edit(caption='',
                             edit_text=self.tracker.format_issue(issue),
                             multiline=True,
                             wrap='clip')
        self.cc_box = Edit(caption='', edit_text='', multiline=True)
        self.block_box = Edit(caption='', edit_text='')
        self.extension = Edit(caption='', edit_text='html')

        products = []
        self.product_info = self.tracker.bzapi.getproducts()
        self.product = None
        self.products_walker = SimpleListWalker([])
        for product in self.product_info:
            if product['is_active']:
                self.products_walker.append(RadioButton(products, product['name'], on_state_change=self.set_product))

        self.component = None
        self.component_box = SimpleFocusListWalker([])

        self.version = None
        self.versions_box = SimpleFocusListWalker([])

        self.result_box = Text(('report_status', ''))

        self.body = SimpleListWalker([Columns([('fixed', 13, Text('Summary: ')), ('weight', 10, self.summary_box)], dividechars=1),
                                      Columns([('fixed', 13, Text('Description: ')), ('weight', 10, self.desc_box)], dividechars=1)])

        dups = self.tracker.find_issue(issue)
        self.dups_walker = None
        if dups:
            options = []
            self.dups_walker = SimpleListWalker([RadioButton(options, 'None')])
            for entry in dups:
                self.dups_walker.append(RadioButton(options, entry.weburl, on_state_change=self.set_duplicate))
            self.body.insert(0, Columns([('fixed', 13, Text('Duplicates: ')), ('weight', 10, BoxAdapter(ListBox(self.dups_walker), height=len(self.dups_walker)))]))

        frame = Frame(#header=AttrMap(Text(issue['id'], align='center'), attr_map='table_header_bg'),
                      body=AttrMap(
                          Columns([
                              ('weight', 10, ListBox(self.body)),
                              ('weight', 3, ListBox(SimpleListWalker([
                                  LineBox(BoxAdapter(ListBox(self.products_walker), height=len(self.products_walker)), title='Products'),
                                  LineBox(BoxAdapter(ListBox(self.component_box), height=10), title='Components'),
                                  LineBox(BoxAdapter(ListBox(self.versions_box), height=10), title='Versions'),
                                  Columns([('weight', 1, Text('CC: ')), ('weight', 4, self.cc_box)]),
                                  Columns([('weight', 1, Text('Blocks: ')), ('weight', 4, self.block_box)]),
                                  Columns([('weight', 1, Text('Ext: ')), ('weight', 4, self.extension)]),
                              ])))])
                      , 'table_header'),
                      footer=Columns([('pack', close_button),
                                      ('pack', report_button),
                                      ('pack', save_button)], dividechars=2),
                      focus_part='body')

        WidgetWrap.__init__(self, AttrMap(PatternBox(frame, title=('dialog_title', issue['id']), **fz_box_pattern()), attr_map='main_bg'))
        self.set_product(self.products_walker.contents[0], True)

    def set_duplicate(self, btn, state):
        if state:
            self.duplicate = btn.label

    def set_product(self, btn, state):
        if state:
            self.product = btn.label
            self.update_components(self.tracker.bzapi.getcomponents(self.product))
            versions = [version['name'] for product in self.product_info if product['name'] == self.product for version in product['versions'] if version['is_active']]
            self.update_versions(versions)

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

    def keypress(self, size, key):
        if key in ['esc', 'f3']:
            self._emit('close')
        else:
            super(BugzillaReportDialog, self).keypress(size, key)

    def report(self, btn):
        report_details = dict(
            product=self.product,
            component=self.component,
            summary=self.summary_box.edit_text,
            version=self.version,
            description=self.desc_box.edit_text,
            blocks=self.block_box.edit_text
        )
        bug = self.tracker.report_issue(report_details=report_details,
                                        extension=self.extension.edit_text)

        self.result_box.set_text('Reported at: {weburl}'.format(weburl=bug.weburl))
        self.tracker.set_reported(self.issue, bug.weburl)
        return bug


class GithubReportDialog(WidgetWrap):
    signals = ['close']

    def __init__(self, issue, tracker):
        self.issue = issue
        self.tracker = tracker

        # TODO: ugly! refactor needed!
        from .widgets import FormattedButton
        report_button = FormattedButton('Report', lambda button: self.report(btn=button))
        close_button = FormattedButton('Close', lambda button: self._emit('close'))

        duplicate_box = None
        dups = self.tracker.find_issue(issue)
        if dups:
            duplicate_box = LineBox(ListBox(SimpleListWalker([
                        Text('* {summary}\n{url}'.format(summary=entry.title, url=entry.html_url)) for entry in dups])))

        title_box = Edit(caption='', edit_text=self.tracker(issue))
        body_box = Edit(caption='', edit_text=self.tracker.format_issue(issue), multiline=True)
        self.result_box = Text(('report_status', ''))

        self.body = SimpleListWalker([
            Columns([('fixed', 10, Text('Title: ')), ('weight', 1, title_box)], dividechars=1),
            Columns([('fixed', 10, Text('Description: ')), ('weight', 1, body_box)], dividechars=1)
        ])

        if duplicate_box:
            self.body.insert(0, duplicate_box)

        frame = Frame(header=AttrMap(Text(issue['id'], align='center'), attr_map='table_header_bg'),
                      body=AttrMap(ListBox(self.body), 'table_header'),
                      footer=Columns([('pack', close_button),
                                      ('pack', report_button)], dividechars=2),
                      focus_part='body')

        WidgetWrap.__init__(self, AttrMap(LineBox(Padding(frame, left=1, right=1)), attr_map='main_bg'))

    def keypress(self, size, key):
        if key in ['esc', 'f3']:
            self._emit('close')
        else:
            super(GithubReportDialog, self).keypress(size, key)

    def report(self, btn):
        bug = self.tracker.report_issue(dict(title=self.title_box.edit_text,
                                             body=self.body_box.edit_text))

        self.result_box.set_text('Reported at: {weburl}'.format(weburl=bug.html_url))
        self.body.insert(0, self.result_box)
        self.tracker.set_reported(self.issue, bug.html_url)
        return bug
