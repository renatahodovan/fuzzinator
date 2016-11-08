# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from os import get_terminal_size
from urwid import *

from .decor_widgets import PatternBox
from .graphics import fz_box_pattern
from .dialogs import Dialog
from .button import FormattedButton


class LoginDialog(Dialog):
    signals = ['close', 'login']

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
    signals = ['click', 'login', 'ready']

    def __init__(self, tracker):
        self.tracker = tracker
        super(LoginButton, self).__init__(FormattedButton('', style='dialog'))
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        pop_up = LoginDialog(self.tracker)
        connect_signal(pop_up, 'close', lambda dialog: self.done())
        connect_signal(pop_up, 'login', lambda p, user, pwd: self._emit('login', (user, pwd)))
        return pop_up

    def get_pop_up_parameters(self):
        cols, rows = get_terminal_size()
        return {'left': 0, 'top': -rows // 2 - 5, 'overlay_width': 50, 'overlay_height': 10}

    def done(self):
        self.close_pop_up()
        self._emit('ready')


class BugzillaReportDialog(PopUpTarget):
    signals = ['close']

    def __init__(self, issue, tracker):
        self.issue = issue
        self.tracker = tracker
        self.duplicate = None

        report_button = FormattedButton('Report', lambda button: self.report(btn=button))
        save_button = FormattedButton('Save as reported', lambda button: self.save_reported())
        close_button = FormattedButton('Close', lambda button: self._emit('close_reporter'))
        login_button = LoginButton(self.tracker)
        connect_signal(login_button, 'ready', lambda btn: self.add_dups())

        self.summary_box = Edit(edit_text=self.tracker.title(issue))
        self.desc_box = Edit(edit_text=self.tracker.format_issue(issue),
                             multiline=True, wrap='clip')
        self.cc_box = Edit(multiline=True)
        self.block_box = Edit()
        self.extension = Edit(edit_text='html')

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

        self.result = Text('')
        self.edit_dups = Edit()
        self.body = SimpleListWalker([Columns([('fixed', 13, Text(('dialog_secondary', 'Summary: '))), ('weight', 10, self.summary_box)], dividechars=1),
                                      Columns([('fixed', 13, Text(('dialog_secondary', 'Description: '))), ('weight', 10, self.desc_box)], dividechars=1)])

        frame = Frame(body=AttrMap(
                          Columns([
                              ('weight', 10, ListBox(self.body)),
                              ('weight', 3, AttrMap(ListBox(SimpleListWalker([
                                  LineBox(BoxAdapter(ListBox(self.products_walker), height=len(self.products_walker)), title='Products'),
                                  LineBox(BoxAdapter(ListBox(self.component_box), height=10), title='Components'),
                                  LineBox(BoxAdapter(ListBox(self.versions_box), height=10), title='Versions'),
                                  Columns([('weight', 1, Text('CC: ')), ('weight', 4, self.cc_box)]),
                                  Columns([('weight', 1, Text('Blocks: ')), ('weight', 4, self.block_box)]),
                                  Columns([('weight', 1, Text('Ext: ')), ('weight', 4, self.extension)]),
                              ])), attr_map='dialog_secondary'))])
                      , 'dialog'),
                      footer=Columns([('pack', close_button),
                                      ('pack', report_button),
                                      ('pack', save_button),
                                      ('pack', login_button)], dividechars=2),
                      focus_part='body')

        super(BugzillaReportDialog, self).__init__(AttrMap(PatternBox(frame, title=('dialog_title', issue['id']), **fz_box_pattern()), attr_map='dialog_border'))
        self.set_product(self.products_walker.contents[0], True)

        if not tracker.logged_in:
            login_button.keypress((0, 0), 'enter')
        else:
            self.add_dups()

    def add_dups(self):
        dups_walker = SimpleListWalker([self.edit_dups])
        options = []
        for entry in self.tracker.find_issue(self.issue):
            dups_walker.append(RadioButton(options, entry.weburl, on_state_change=self.set_duplicate))
        self.body.insert(0, Columns([('fixed', 13, Text(('dialog_secondary', 'Duplicates: '))),
                                     ('weight', 10, BoxAdapter(ListBox(dups_walker), height=len(dups_walker)))]))

    def save_reported(self):
        if self.edit_dups.text:
            self.tracker.set_reported(self.issue, self.edit_dups.text)
        elif self.duplicate:
            self.tracker.set_reported(self.issue, self.duplicate)
        self._emit('close')

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
                                        test=self.issue['test'],
                                        extension=self.extension.edit_text)

        self.result.set_text(('dialog_secondary', 'Reported at: {weburl}'.format(weburl=bug.weburl)))
        self.tracker.set_reported(self.issue, bug.weburl)
        return bug


class GithubReportDialog(PopUpTarget):
    signals = ['close']

    def __init__(self, issue, tracker):
        self.issue = issue
        self.tracker = tracker
        self.duplicate = None

        title_box = Edit(caption='', edit_text=self.tracker.title(issue))
        body_box = Edit(caption='', edit_text=self.tracker.format_issue(issue), multiline=True)

        report_button = FormattedButton('Report', on_press=self.report, user_data=(title_box, body_box))
        close_button = FormattedButton('Close', lambda button: self._emit('close'))
        save_button = FormattedButton('Save as reported', lambda button: self.save_reported())
        login_button = LoginButton(self.tracker)
        connect_signal(login_button, 'ready', lambda btn: self.add_dups())

        self.result = Text('')
        self.edit_dups = Edit('')
        self.body = SimpleListWalker([
            Columns([('fixed', 10, Text('Title: ')), ('weight', 1, title_box)], dividechars=1),
            Columns([('fixed', 10, Text('Description: ')), ('weight', 1, body_box)], dividechars=1)
        ])

        frame = Frame(body=AttrMap(ListBox(self.body), 'dialog'),
                      footer=Columns([('pack', close_button),
                                      ('pack', report_button),
                                      ('pack', save_button),
                                      ('pack', login_button)], dividechars=2),
                      focus_part='body')
        super(GithubReportDialog, self).__init__(AttrMap(PatternBox(frame, title=('dialog_title', issue['id']), **fz_box_pattern()), attr_map='dialog_border'))

        if not self.tracker.logged_in:
            login_button.keypress((0, 0), 'enter')
        else:
            self.add_dups()

    def keypress(self, size, key):
        if key in ['esc', 'f3']:
            self._emit('close')
        else:
            super(GithubReportDialog, self).keypress(size, key)

    def save_reported(self):
        if self.edit_dups.text:
            self.tracker.set_reported(self.issue, self.edit_dups.text)
        elif self.duplicate:
            self.tracker.set_reported(self.issue, self.duplicate)
        self._emit('close')

    def set_duplicate(self, btn, state):
        if state:
            self.duplicate = btn.label

    def report(self, _, details):
        bug = self.tracker.report_issue(dict(title=details[0].edit_text,
                                             body=details[1].edit_text))

        self.result.set_text(('dialog_secondary', 'Reported at: {weburl}'.format(weburl=bug.html_url)))
        self.body.insert(0, self.result)
        self.tracker.set_reported(self.issue, bug.html_url)
        return bug

    def add_dups(self):
        dups_walker = SimpleListWalker([self.edit_dups])
        options = []
        for entry in self.tracker.find_issue(self.issue):
            dups_walker.append(RadioButton(options, entry.html_url, on_state_change=self.set_duplicate))
        self.body.insert(0, Columns([('fixed', 13, Text(('dialog_secondary', 'Duplicates: '))),
                                     ('weight', 10, BoxAdapter(ListBox(dups_walker), height=len(dups_walker)))]))
