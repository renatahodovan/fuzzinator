# Copyright (c) 2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class FormatterDecorator(object):
    """
    Abstract base class of formatter decorators (that change the behavior of the
    ``__call__`` method of the :class:`Formatter`).
    """

    def decorate(self, call):
        """
        Return a decorated version of ``call``, which is the ``__call__`` method
        of the decorated issue formatter.

        Raises :exc:`NotImplementedError` by default.

        :param call: The ``__call__`` method to decorate.
        :return: The decorated version of the method.
        """
        raise NotImplementedError()

    def __call__(self, formatter_class):
        """
        Return a decorated version of ``formatter_class``. Create a sub-class of
        ``formatter_class`` and apply :meth:`decorate` on its ``__call__``
        method.

        :param Formatter formatter_class: The issue formatter to decorate.
        :return: The decorated version of the issue formatter.
        :rtype: Formatter
        """

        class DecoratedFormatter(formatter_class):
            @self.decorate
            def __call__(self, *, issue, format='long'):
                return super().__call__(issue=issue, format=format)

        return DecoratedFormatter
