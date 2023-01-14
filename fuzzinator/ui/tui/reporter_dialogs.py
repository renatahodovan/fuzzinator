# Copyright (c) 2016-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging

from urwid import *

from ...config import config_get_object
from ...formatter import JsonFormatter
from ...tracker import TrackerError
from .button import FormattedButton
from .decor_widgets import PatternBox
from .dialogs import BugEditor
from .graphics import fz_box_pattern

logger = logging.getLogger(__name__)


class ReportDialog(PopUpTarget):
    """
    Base class of dialogs that allow preparing an issue report on the
    Urwid_/text-based UI.

    .. _Urwid: https://github.com/urwid/urwid
    """

    signals = ['close']

    def __init__(self, *, issue, config, db):
        """
        Notes:

          - A new dialog is instantiated for every report.
          - Instead of ``__init__``, the :meth:`init` method must be overridden
            in sub-classes.
        """
        self.issue = issue
        self.db = db

        self.tracker = config_get_object(config, f'sut.{issue["sut"]}', 'tracker')
        self.settings = self.tracker.settings()

        formatter = config_get_object(config, f'sut.{issue["sut"]}', 'formatter') or JsonFormatter()
        self.issue_title = BugEditor(edit_text=formatter.summary(issue=issue))
        self.issue_desc = BugEditor(edit_text=formatter(issue=issue), multiline=True, wrap='clip')

        self.duplicate = None
        self.edit_dups = BugEditor()
        dups_walker = SimpleListWalker([self.edit_dups])
        dups = []
        try:
            for dup_url, _ in self.tracker.find_duplicates(title=self.issue_title.get_text()[0]):
                radio_btn = RadioButton(dups, dup_url, on_state_change=self.set_duplicate)
                # Select the first suggested bug if there is not set any.
                if self.duplicate is None:
                    self.duplicate = radio_btn.label
                dups_walker.append(radio_btn)
        except TrackerError as e:
            logger.warning(str(e), exc_info=e)
        body = SimpleListWalker([Columns([('fixed', 13, Text(('dialog_secondary', 'Duplicates: '))),
                                          ('weight', 10, BoxAdapter(ListBox(dups_walker), height=len(dups_walker)))]),
                                 Columns([('fixed', 13, Text(('dialog_secondary', 'Summary: '))),
                                          ('weight', 10, self.issue_title)], dividechars=1),
                                 Columns([('fixed', 13, Text(('dialog_secondary', 'Description: '))),
                                          ('weight', 10, self.issue_desc)], dividechars=1)])
        self.settings_walker = SimpleListWalker([])
        frame = Frame(body=AttrMap(Columns([('weight', 10, ListBox(body)),
                                            ('weight', 3, AttrMap(ListBox(self.settings_walker), attr_map='dialog_secondary'))]),
                                   'dialog'),
                      footer=Columns([('pack', FormattedButton('Close', lambda button: self._emit('close_reporter'))),
                                      ('pack', FormattedButton('Report', lambda button: self.send_report())),
                                      ('pack', FormattedButton('Save as reported', lambda button: self.save_reported()))], dividechars=2),
                      focus_part='body')

        super().__init__(AttrMap(PatternBox(frame, title=('dialog_title', issue['id']), **fz_box_pattern()), attr_map='dialog_border'))
        self.init()

    def init(self):
        """
        This method is called to finish initialization after ``__init__`` sets
        up the basic layout of the dialog. Sub-classes shall override this
        method if they want to add extra UI elements to the dialog to get input
        from the user that is necessary to submit the issue report to the
        tracker.

        This method is a no-op by default, therefore sub-classes don't have to
        invoke it from the overridden version.

        Information about the issue to be reported and about the tracker, and UI
        extension points are available as instance variables.

        :ivar dict[str, Any] issue: the issue to be reported.
        :ivar Any settings: the tracker-specific information returned by
            :meth:`fuzzinator.tracker.Tracker.settings`.
        :ivar urwid.SimpleListWalker settings_walker: a list that can be
            extended with Urwid UI components to display information to and
            collect input from the user, usually based on ``settings`` (empty by
            default).
        """
        pass

    def set_duplicate(self, btn, state):
        if state:
            self.duplicate = btn.label

    def send_report(self):
        try:
            issue_url = self.tracker.report_issue(**self.data())
            self.db.update_issue_by_oid(self.issue['_id'], {'reported': issue_url})
        except TrackerError as e:
            logger.error(str(e), exc_info=e)

    def save_reported(self):
        if self.edit_dups.text:
            url = self.edit_dups.text
        elif self.duplicate:
            url = self.duplicate
        else:
            url = ''
        self.db.update_issue_by_oid(self.issue['_id'], {'reported': url})
        self._emit('close')

    def keypress(self, size, key):
        if key in ['esc', 'f7']:
            self._emit('close')
            return None
        return super().keypress(size, key)

    def data(self):
        """
        Return a dictionary that contains data that shall be reported to the
        issue tracker. The items in the dictionary will be passed as keyword
        arguments to :meth:`fuzzinator.tracker.Tracker.report_issue`. Therefore,
        the dictionary must contain values with keys ``'title'`` and ``'body'``.

        The default operation is to return a dictionary that contains the
        (potentially user-edited) short and full string representations of the
        issue-to-be-reported assigned to ``'title'`` and ``'body'``,
        respectively.

        Sub-classes may override this method, where they call this original
        operation to build the default dictionary and then extend it with
        additional fields (usually with information coming from extra UI
        elements set up in :meth:`init`), as expected by the corresponding
        :class:`~fuzzinator.tracker.Tracker`.

        :return: the data to be reported to the issue tracker.
        :rtype: dict
        """
        return dict(title=self.issue_title.edit_text,
                    body=self.issue_desc.edit_text)


class BugzillaReportDialog(ReportDialog):

    def init(self):
        self.edit_blocks = BugEditor()
        self.edit_extension = BugEditor(edit_text='html')

        self.product = None
        products_walker = SimpleListWalker([])
        products = []
        for product in self.settings:
            products_walker.append(RadioButton(products, product, on_state_change=self.set_product))

        self.component = None
        self.component_box = SimpleFocusListWalker([])

        self.version = None
        self.versions_box = SimpleFocusListWalker([])

        self.settings_walker.extend([LineBox(BoxAdapter(ListBox(products_walker), height=len(products_walker)), title='Products'),
                                     LineBox(BoxAdapter(ListBox(self.component_box), height=10), title='Components'),
                                     LineBox(BoxAdapter(ListBox(self.versions_box), height=10), title='Versions'),
                                     Columns([('weight', 1, Text('Blocks: ')), ('weight', 4, self.edit_blocks)]),
                                     Columns([('weight', 1, Text('Ext: ')), ('weight', 4, self.edit_extension)])])

        self.set_product(products_walker.contents[0], True)

    def set_product(self, btn, state):
        if state:
            self.product = btn.label
            self.update_components(self.settings[self.product]['components'])
            self.update_versions(self.settings[self.product]['versions'])

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

    def data(self):
        data = super().data()
        data.update(product=self.product,
                    product_version=self.version,
                    component=self.component,
                    blocks=self.edit_blocks.edit_text,
                    test=self.issue['test'],
                    extension=self.edit_extension.edit_text)
        return data
