# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from os import get_terminal_size

from inators.imp import import_object
from urwid import *

from ...config import config_get_object
from .button import FormattedButton
from .dialogs import AboutDialog, EditIssueDialog, FormattedIssueDialog
from .reporter_dialogs import ReportDialog


class FullScreenPopupLauncher(PopUpLauncher):

    def get_pop_up_parameters(self):
        cols, rows = get_terminal_size()
        return {'left': cols // 2, 'top': rows // 2, 'overlay_width': cols, 'overlay_height': rows}


class AboutButton(PopUpLauncher):

    def __init__(self, label):
        super().__init__(FormattedButton(label))
        self.about = AboutDialog()
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def get_pop_up_parameters(self):
        width = max(len(line) for line in self.about.content.splitlines()) + 10
        height = self.about.content.count('\n') + 4
        cols, rows = get_terminal_size()
        return dict(left=max(cols // 2 - width // 2, 1),
                    top=min(-rows // 2 - height // 2, -1),
                    overlay_width=width,
                    overlay_height=height)

    def create_pop_up(self):
        connect_signal(self.about, 'close', lambda button: self.close_pop_up())
        return self.about


class ViewButton(FullScreenPopupLauncher):

    def __init__(self, label, issues_table, config):
        super().__init__(FormattedButton(label))
        self.issues_table = issues_table
        self.config = config
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None

        pop_up = FormattedIssueDialog(config=self.config,
                                      issue=self.issues_table.db.find_issue_by_oid(focus.data['_id']),
                                      db=self.issues_table.db)
        connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up


class EditButton(FullScreenPopupLauncher):

    def __init__(self, label, issues_table):
        super().__init__(FormattedButton(label))
        self.issues_table = issues_table
        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def create_pop_up(self):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None

        pop_up = EditIssueDialog(issue=self.issues_table.db.find_issue_by_oid(focus.data['_id']),
                                 db=self.issues_table.db)
        connect_signal(pop_up, 'close', lambda button: self.close_pop_up())
        return pop_up


class ReportButton(FullScreenPopupLauncher):

    def __init__(self, label, issues_table, config):
        super().__init__(FormattedButton(label))
        self.issues_table = issues_table
        self.config = config

        connect_signal(self.original_widget, 'click', lambda btn: self.open_pop_up())

    def update_entry(self, issue_oid):
        self.issues_table.update_row(issue_oid)
        self.close_pop_up()

    def create_pop_up(self):
        focus = self.issues_table.listbox.focus
        if not focus:
            return None
        issue = self.issues_table.db.find_issue_by_oid(focus.data['_id'])

        tracker = config_get_object(self.config, f'sut.{issue["sut"]}', 'tracker')
        if tracker:
            dialog = tracker.ui_extension.get('tui')
            popup_cls = import_object(dialog) if dialog else ReportDialog
        else:
            # If there is no tracker then we only display the formatted issue.
            popup_cls = FormattedIssueDialog

        pop_up = popup_cls(issue=issue, config=self.config, db=self.issues_table.db)
        connect_signal(pop_up, 'close', lambda button: self.update_entry(focus.data['_id']))
        return pop_up
