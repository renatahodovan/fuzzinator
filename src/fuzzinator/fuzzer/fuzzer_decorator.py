# Copyright (c) 2021-2023 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

from inspect import signature


class FuzzerDecorator:
    """
    Base class for :class:`Fuzzer` decorators.
    """

    def init(self, cls, obj, **kwargs):
        """
        Initialize ``obj`` of type ``cls``. The default operation is to call the
        ``__init__`` method of the original version of the fuzzer class.

        Subclasses of :class:`FuzzerDecorator` may override this method if
        customization of the initialization is needed. Usually, the overridden
        method has to call the original ``__init__`` at some point, which can
        be performed either by ``super().init(cls, obj, **kwargs)`` (which will
        call this method, and then transitively the original ``__init__``) or by
        ``super(cls, obj).__init__(**kwargs)`` (which calls the original
        ``__init__`` directly).

        :param cls: The decorated version of the fuzzer class, as returned by
            :meth:`__call__`.
        :param obj: The fuzzer instance to initialize.
        """
        super(cls, obj).__init__(**kwargs)

    def enter(self, cls, obj):
        """
        Enter the context managed by ``obj`` of type ``cls``. The default
        operation is to call the ``__enter__`` method of the original version of
        the fuzzer class and return its result.

        Subclasses of :class:`FuzzerDecorator` may override this method if
        customization of entering the context is needed. Usually, the overridden
        method has to call the original ``__enter__`` at some point, which can
        be performed either by ``super().enter(cls, obj)`` (which will call this
        method, and then transitively the original ``__enter__``) or by
        ``super(cls, obj).__enter__()`` (which calls the original ``__enter__``
        directly).

        :param cls: The decorated version of the fuzzer class, as returned by
            :meth:`__call__`.
        :param obj: The fuzzer instance managing the context.
        :return: A value as defined by the context management protocol (usually,
            ``obj``).
        """
        return super(cls, obj).__enter__()

    def exit(self, cls, obj, *exc):
        """
        Exit the context managed by ``obj`` of type ``cls``. The default
        operation is to call the ``__exit__`` method of the original version of
        the fuzzer class and return its result.

        Subclasses of :class:`FuzzerDecorator` may override this method if
        customization of exiting the context is needed. Usually, the overridden
        method has to call the original ``__exit__`` at some point, which can
        be performed either by ``super().exit(cls, obj, *exc)`` (which will call
        this method, and then transitively the original ``__exit__``) or by
        ``super(cls, obj).__exit__(*exc)`` (which calls the original
        ``__exit__`` directly).

        :param cls: The decorated version of the fuzzer class, as returned by
            :meth:`__call__`.
        :param obj: The fuzzer instance managing the context.
        :param exc: The exception that caused the context to be exited (if any),
            as defined by the context management protocol.
        :return: Whether to suppress the exception in ``exc``, as defined by the
            context management protocol.
        """
        return super(cls, obj).__exit__(*exc)

    def call(self, cls, obj, *, index):
        """
        Call ``obj`` of type ``cls``. The default operation is to call the
        ``__call__`` method of the original version of the fuzzer class and
        return its result.

        Subclasses of :class:`FuzzerDecorator` may override this method if
        customization of calling the fuzzer is needed. Usually, the overridden
        method has to call the original ``__call__`` at some point, which can
        be performed either by ``super().call(cls, obj, index=index)`` (which
        will call this method, and then transitively the original ``__call__``)
        or by ``super(cls, obj).__call__(index=index)`` (which calls the
        original ``__call__`` directly).

        :param cls: The decorated version of the fuzzer class, as returned by
            :meth:`__call__`.
        :param obj: The fuzzer instance to invoke.
        :param index: A running counter, as defined by :meth:`Fuzzer.__call__`.
        :return: The generated test case, as defined by :meth:`Fuzzer.__call__`.
        """
        return super(cls, obj).__call__(index=index)

    def __call__(self, fuzzer_class):
        """
        Return a decorated version of ``fuzzer_class``. Create a subclass of
        ``fuzzer_class`` that transfers control to :meth:`init`, :meth:`enter`,
        :meth:`exit`, or :meth:`call` when its ``__init__``, ``__enter__``,
        ``__exit__``, or ``__call__`` methods are invoked.

        :param fuzzer_class: The fuzzer class to decorate.
        :return: The decorated version of the fuzzer class.
        """
        decorator = self

        class DecoratedFuzzer(fuzzer_class):

            def __init__(self, **kwargs):
                signature(self.__init__).bind(**kwargs)
                decorator.init(DecoratedFuzzer, self, **kwargs)
            __init__.__signature__ = signature(fuzzer_class.__init__)

            def __enter__(self):
                return decorator.enter(DecoratedFuzzer, self)

            def __exit__(self, *exc):
                return decorator.exit(DecoratedFuzzer, self, *exc)

            def __call__(self, *, index):
                return decorator.call(DecoratedFuzzer, self, index=index)

        return DecoratedFuzzer
