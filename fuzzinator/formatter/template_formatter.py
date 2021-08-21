# Copyright (c) 2018-2022 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from ..config import as_path
from .formatter import Formatter


class TemplateFormatter(Formatter):
    """
    Abstract base class of template-based formatters.

    The concept of formatters is to provide a way of custom issue visualization.
    Issues can be rendered differently when they are sent via e-mail, displayed
    in TUI, or inserted into a report for an arbitrary issue tracker.

    Every formatter class must support two formats: a short and a long version.
    The short version (returned by :meth:`Formatter.summary`) acts as a summary
    of the issue, e.g., the subject of an email, while the long version
    (returned by :meth:`Formatter.__call__`) can give a detailed description
    about the failure, e.g., the body of an issue report.

    The subclasses of :class:`TemplateFormatter` can define templates for the
    two formats either by a plain string in the format expected by the chosen
    template class (with the ``short`` and ``long`` parameters) or by a file
    containing such a string content (through the ``short_file`` and
    ``long_file`` options).

    Note: if a template is defined both by plain string and through file, then
    the file content will be used.
    """

    def __init__(self, *, short='', short_file=None, long='', long_file=None):
        if short_file:
            with open(as_path(short_file), 'r') as f:
                short = f.read()
        self.short_template = short

        if long_file:
            with open(as_path(long_file), 'r') as f:
                long = f.read()
        self.long_template = long

    def render(self, *, issue, template):
        """
        Render the string representation of ``issue`` with the help of
        ``template``.

        Raises :exc:`NotImplementedError` by default.

        :param dict[str, Any] issue: The issue to be formatted.
        :param str template: The template to use for formatting.
        :return: The string representation of the issue.
        :rtype: str
        """
        raise NotImplementedError()

    def __call__(self, *, issue):
        return self.render(issue=issue, template=self.long_template)

    def summary(self, *, issue):
        return self.render(issue=issue, template=self.short_template)
