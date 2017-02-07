# Copyright (c) 2016-2017 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from os import get_terminal_size
from urwid import *

from .decor_widgets import PatternBox
from .graphics import fz_box_pattern
from .dialogs import Dialog, BugEditor
from .button import FormattedButton


class LoginDialog(Dialog):
    signals = ['close']

    def __init__(self, tracker):
        self.tracker = tracker
        name = Edit(caption='Username: ', edit_text='')
        pwd = Edit(caption='Password: ', edit_text='', mask='*')
        self.result = Text('')
        super(LoginDialog, self).__init__(title='Login',
                                          body=[self.result, name, pwd],
                                          footer_btns=[FormattedButton(label='Login',
                                                                       on_press=self.send_credentials,
                                                                       user_data=(name, pwd)),
                                                       FormattedButton(label='Cancel', on_press=lambda btn: self._emit('close'))])

    def send_credentials(self, _, details):
        result = self.tracker.login(details[0].edit_text, details[1].edit_text)
        if not result:
            self.result.set_text(('warning', 'Login failed!'))
        else:
            self._emit('close')


class LoginButton(PopUpLauncher):
    signals = ['click', 'ready']

    def __init__(self, tracker):
        self.tracker = tracker
        super(LoginButton, self).__init__(FormattedButton('', style='dialog'))
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        pop_up = LoginDialog(self.tracker)
        connect_signal(pop_up, 'close', lambda dialog: self.done())
        return pop_up

    def get_pop_up_parameters(self):
        cols, rows = get_terminal_size()
        return {'left': 0, 'top': -rows // 2 - 5, 'overlay_width': 50, 'overlay_height': 10}

    def done(self):
        self.close_pop_up()
        self._emit('ready')


class ReportDialog(PopUpTarget):
    signals = ['close']

    def __init__(self, issue, tracker, db, side_bar=None):
        self.issue = issue
        self.tracker = tracker
        self.db = db
        self.duplicate = None

        self.edit_dups = BugEditor()
        self.result = Text('')
        self.issue_title = BugEditor(edit_text=self.tracker.title(issue))
        self.issue_desc = BugEditor(edit_text=self.tracker.format_issue(issue), multiline=True, wrap='clip')
        self.body = SimpleListWalker([Columns([('fixed', 13, Text(('dialog_secondary', 'Summary: '))),
                                               ('weight', 10, self.issue_title)], dividechars=1),
                                      Columns([('fixed', 13, Text(('dialog_secondary', 'Description: '))),
                                               ('weight', 10, self.issue_desc)], dividechars=1)])

        login_button = LoginButton(self.tracker)
        connect_signal(login_button, 'ready', lambda btn: self.find_duplicates())
        frame = Frame(body=AttrMap(Columns([('weight', 10, ListBox(self.body)),
                                            ('weight', 3, AttrMap(ListBox(SimpleListWalker(side_bar or [])), attr_map='dialog_secondary'))]),
                                   'dialog'),
                      footer=Columns([('pack', FormattedButton('Close', lambda button: self._emit('close_reporter'))),
                                      ('pack', FormattedButton('Report', lambda button: self.send_report())),
                                      ('pack', FormattedButton('Save as reported', lambda button: self.save_reported())),
                                      ('pack', login_button)], dividechars=2),
                      focus_part='body')

        super(ReportDialog, self).__init__(AttrMap(PatternBox(frame, title=('dialog_title', issue['id']), **fz_box_pattern()), attr_map='dialog_border'))
        if not self.tracker.logged_in:
            login_button.keypress((0, 0), 'enter')
        else:
            self.find_duplicates()

    def set_duplicate(self, btn, state):
        if state:
            self.duplicate = btn.label

    def find_duplicates(self):
        dups_walker = SimpleListWalker([self.edit_dups])
        options = []
        for entry in self.tracker.find_issue(self.issue):
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
        self.db.update_issue(self.issue, {'reported': url})
        return url

    def save_reported(self):
        if self.edit_dups.text:
            url = self.edit_dups.text
        elif self.duplicate:
            url = self.duplicate
        else:
            url = ''
        self.db.update_issue(self.issue, {'reported': url})
        self._emit('close')

    def keypress(self, size, key):
        if key in ['esc', 'f7']:
            self._emit('close')
        else:
            super(ReportDialog, self).keypress(size, key)


class BugzillaReportDialog(ReportDialog):

    def __init__(self, issue, tracker, db):
        self.edit_blocks = BugEditor()
        self.edit_cc = BugEditor(multiline=True)
        self.edit_extension = BugEditor(edit_text='html')

        self.product_info = tracker.bzapi.getproducts()
        self.product = None
        products_walker = SimpleListWalker([])
        products = []
        for product in self.product_info:
            if product['is_active']:
                products_walker.append(RadioButton(products, product['name'], on_state_change=self.set_product))

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

        super(BugzillaReportDialog, self).__init__(issue=issue, tracker=tracker, db=db, side_bar=side_bar)
        self.set_product(products_walker.contents[0], True)

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

    def get_report_data(self):
        return dict(
            report_details=dict(
                product=self.product,
                component=self.component,
                summary=self.issue_title.edit_text,
                version=self.version,
                description=self.issue_desc.edit_text,
                blocks=self.edit_blocks.edit_text
            ),
            test=self.issue['test'],
            extension=self.edit_extension.edit_text
        )


class GithubReportDialog(ReportDialog):

    def get_report_data(self):
        return dict(title=self.issue_title.edit_text,
                    body=self.issue_desc.edit_text)


class MonorailReportDialog(ReportDialog):

    def get_report_data(self):
        return dict(title=self.issue_title.edit_text,
                    body=self.issue_desc.edit_text)
