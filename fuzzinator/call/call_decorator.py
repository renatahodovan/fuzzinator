# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from inspect import signature


class CallDecorator(object):
    """
    Base class for SUT call (i.e., :class:`Call`) decorators.
    """

    def init(self, cls, obj, **kwargs):
        """
        Initialize ``obj`` of type ``cls``. The default operation is to call the
        ``__init__`` method of the original version of the SUT call class.

        Subclasses of :class:`CallDecorator` may override this method if
        customization of the initialization is needed. Usually, the overridden
        method has to call the original ``__init__`` at some point, which can
        be performed either by ``super().init(cls, obj, **kwargs)`` (which will
        call this method, and then transitively the original ``__init__``) or by
        ``super(cls, obj).__init__(**kwargs)`` (which calls the original
        ``__init__`` directly).

        :param cls: The decorated version of the SUT call class, as returned by
            :meth:`__call__`.
        :param obj: The SUT call instance to initialize.
        """
        super(cls, obj).__init__(**kwargs)

    def enter(self, cls, obj):
        """
        Enter the context managed by ``obj`` of type ``cls``. The default
        operation is to call the ``__enter__`` method of the original version of
        the SUT call class and return its result.

        Subclasses of :class:`CallDecorator` may override this method if
        customization of entering the context is needed. Usually, the overridden
        method has to call the original ``__enter__`` at some point, which can
        be performed either by ``super().enter(cls, obj)`` (which will call this
        method, and then transitively the original ``__enter__``) or by
        ``super(cls, obj).__enter__()`` (which calls the original ``__enter__``
        directly).

        :param cls: The decorated version of the SUT call class, as returned by
            :meth:`__call__`.
        :param obj: The SUT call instance managing the context.
        :return: A value as defined by the context management protocol (usually,
            ``obj``).
        """
        return super(cls, obj).__enter__()

    def exit(self, cls, obj, *exc):
        """
        Exit the context managed by ``obj`` of type ``cls``. The default
        operation is to call the ``__exit__`` method of the original version of
        the SUT call class and return its result.

        Subclasses of :class:`CallDecorator` may override this method if
        customization of exiting the context is needed. Usually, the overridden
        method has to call the original ``__exit__`` at some point, which can
        be performed either by ``super().exit(cls, obj, *exc)`` (which will call
        this method, and then transitively the original ``__exit__``) or by
        ``super(cls, obj).__exit__(*exc)`` (which calls the original
        ``__exit__`` directly).

        :param cls: The decorated version of the SUT call class, as returned by
            :meth:`__call__`.
        :param obj: The SUT call instance managing the context.
        :param exc: The exception that caused the context to be exited (if any),
            as defined by the context management protocol.
        :return: Whether to suppress the exception in ``exc``, as defined by the
            context management protocol.
        """
        return super(cls, obj).__exit__(*exc)

    def call(self, cls, obj, *, test, **kwargs):
        """
        Call ``obj`` of type ``cls``. The default operation is to call the
        ``__call__`` method of the original version of the SUT call class and
        return its result.

        Subclasses of :class:`CallDecorator` may override this method if
        customization of calling the SUT is needed. Usually, the overridden
        method has to call the original ``__call__`` at some point, which can
        be performed either by ``super().call(cls, obj, test=test, **kwargs)``
        (which will call this method, and then transitively the original
        ``__call__``) or by ``super(cls, obj).__call__(test=test, **kwargs)``
        (which calls the original ``__call__`` directly).

        :param cls: The decorated version of the SUT call class, as returned by
            :meth:`__call__`.
        :param obj: The SUT call instance to invoke.
        :param test: Input or test case for the SUT call, as defined by
            :meth:`Call.__call__`.
        :return: The result of the SUT call, as defined by
            :meth:`Call.__call__`.
        """
        return super(cls, obj).__call__(test=test, **kwargs)

    def __call__(self, call_class):
        """
        Return a decorated version of ``call_class``. Create a subclass of
        ``call_class`` that transfers control to :meth:`init`, :meth:`enter`,
        :meth:`exit`, or :meth:`call` when its ``__init__``, ``__enter__``,
        ``__exit__``, or ``__call__`` methods are invoked.

        :param call_class: The SUT call class to decorate.
        :return: The decorated version of the SUT call class.
        """
        decorator = self

        class DecoratedCall(call_class):

            def __init__(self, **kwargs):
                signature(self.__init__).bind(**kwargs)
                decorator.init(DecoratedCall, self, **kwargs)
            __init__.__signature__ = signature(call_class.__init__)

            def __enter__(self):
                return decorator.enter(DecoratedCall, self)

            def __exit__(self, *exc):
                return decorator.exit(DecoratedCall, self, *exc)

            def __call__(self, *, test, **kwargs):
                return decorator.call(DecoratedCall, self, test=test, **kwargs)

        return DecoratedCall
