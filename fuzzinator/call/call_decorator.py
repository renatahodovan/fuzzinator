# Copyright (c) 2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.


class CallDecorator(object):
    """
    Abstract base class for SUT call decorators that only change the behavior of
    the ``__call__`` method of the :class:`Call`.
    """

    def decorate(self, call):
        """
        Return a decorated version of ``call``, which is the ``__call__`` method
        of the decorated SUT call.

        Raises :exc:`NotImplementedError` by default.

        :param call: The ``__call__`` method to decorate.
        :return: The decorated version of the method.
        """
        raise NotImplementedError()

    def __call__(self, call_class):
        """
        Return a decorated version of ``call_class``. Create a sub-class of
        ``call_class`` and apply :meth:`decorate` on its ``__call__`` method.

        :param Call call_class: The SUT call to decorate.
        :return: The decorated version of the SUT call.
        :rtype: Call
        """

        class DecoratedCall(call_class):
            @self.decorate
            def __call__(self, *, test, **kwargs):
                return super().__call__(test=test, **kwargs)

        return DecoratedCall
