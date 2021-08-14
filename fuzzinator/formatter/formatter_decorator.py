# Copyright (c) 2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from inspect import signature


class FormatterDecorator(object):
    """
    Base class for :class:`Formatter` decorators.
    """

    def init(self, cls, obj, **kwargs):
        """
        Initialize ``obj`` of type ``cls``. The default operation is to call the
        ``__init__`` method of the original version of the formatter class.

        Sub-classes of :class:`FormatterDecorator` may override this method if
        customization of the initialization is needed. Usually, the overridden
        method has to call the original ``__init__`` at some point, which can
        be performed either by ``super().init(cls, obj, **kwargs)`` (which will
        call this method, and then transitively the original ``__init__``) or by
        ``super(cls, obj).__init__(**kwargs)`` (which calls the original
        ``__init__`` directly).

        :param cls: The decorated version of the formatter class, as returned by
            :meth:`__call__`.
        :param obj: The issue formatter instance to initialize.
        """
        super(cls, obj).__init__(**kwargs)

    def call(self, cls, obj, *, issue, format='long'):
        """
        Call ``obj`` of type ``cls``. The default operation is to call the
        ``__call__`` method of the original version of the formatter class and
        return its result.

        Sub-classes of :class:`FormatterDecorator` may override this method if
        customization of calling the formatter is needed. Usually, the
        overridden method has to call the original ``__call__`` at some point,
        which can be performed either by
        ``super().call(cls, obj, issue=issue, format=format)`` (which will call
        this method, and then transitively the original ``__call__``) or by
        ``super(cls, obj).__call__(issue=issue, format=format)`` (which calls
        the original ``__call__`` directly).

        :param cls: The decorated version of the formatter class, as returned by
            :meth:`__call__`.
        :param obj: The issue formatter instance to invoke.
        :param issue: The issue to be formatted, as defined by
            :meth:`Formatter.__call__`.
        :param format: The formatting instruction, as defined by
            :meth:`Formatter.__call__`.
        :return: The string representation of the issue, as defined by
            :meth:`Formatter.__call__`.
        """
        return super(cls, obj).__call__(issue=issue, format=format)

    def __call__(self, formatter_class):
        """
        Return a decorated version of ``formatter_class``. Create a sub-class of
        ``formatter_class`` that transfers control to :meth:`init` or
        :meth:`call` when its ``__init__`` or ``__call__`` methods are invoked.

        :param formatter_class: The issue formatter class to decorate.
        :return: The decorated version of the issue formatter class.
        """
        decorator = self

        class DecoratedFormatter(formatter_class):

            def __init__(self, **kwargs):
                signature(self.__init__).bind(**kwargs)
                decorator.init(DecoratedFormatter, self, **kwargs)
            __init__.__signature__ = signature(formatter_class.__init__)

            def __call__(self, *, issue, format='long'):
                return decorator.call(DecoratedFormatter, self, issue=issue, format=format)

        return DecoratedFormatter
