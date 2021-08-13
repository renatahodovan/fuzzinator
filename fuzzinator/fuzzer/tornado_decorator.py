# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import asyncio
import logging
import ssl
import threading

try:
    from asyncio import all_tasks as asyncio_all_tasks  # from py39, asyncio.Task.all_tasks is deprecated
except ImportError:
    asyncio_all_tasks = asyncio.Task.all_tasks  # pylint: disable=no-member
from inspect import signature

from tornado.ioloop import IOLoop
from tornado.testing import bind_unused_port
from tornado.web import Application, RequestHandler

logger = logging.getLogger(__name__)


class TornadoDecorator(object):
    """
    Decorator for fuzzers to transport generated content through http. It is
    useful for transporting fuzz tests to browser SUTs.

    The decorator starts a Tornado server at the start of the fuzz job and
    returns an http url as test input. If the SUT accesses the domain root
    through a GET request, then the decorated fuzzer is invoked and the
    response is the generated test. Accessing other paths can return static
    or dynamically rendered content.

    When the certfile and possibly also the keyfile optional parameters are
    defined, the traffic will be served through SSL.

    **Optional parameters of the fuzzer decorator:**

      - ``template_path``: Directory containing .html template files. These are
        served from the path ``/`` without the .html extension.
      - ``static_path``: Directory from which static files will be served.
        These are served from the path ``/static/``.
      - ``url``: Url template with ``{port}`` and ``{index}`` placeholders, that
        will be filled in with appropriate values. This is the url that will be
        served for the SUT as the test case.
        (Default: ``http(s)://localhost:{port}?index={index}``)
      - ``refresh``: Integer number denoting the time interval (in seconds)
        for the document at the root path (i.e., the test case) to refresh
        itself. Setting it to 0 means no refresh. (Default: 0)
      - ``certfile``: Path to a PEM file containing the certificate needed
        to establish the certificate’s authenticity (Default: None).
      - ``keyfile``: Path to a file containing the private key (Default: None).

    **Example configuration snippet:**

        .. code-block:: ini

            [sut.foo]
            # assuming that foo expects a http url as input, which it tries to access
            # afterwards

            [fuzz.foo-with-bar-over-http]
            sut=foo
            #fuzzer=...
            fuzzer.decorate(0)=fuzzinator.fuzzer.TornadoDecorator
            batch=5

            [fuzz.foo-with-bar-over-http.fuzzer.decorate(0)]
            template_path=/home/lili/fuzzer/templates/
            static_path=/home/lili/fuzzer/static/
            # assuming that there is a main.html in the template_path directory
            url=http://localhost:{port}/main?index={index}
            refresh=3
    """

    def __init__(self, *, template_path=None, static_path=None, url=None, refresh=None, certfile=None, keyfile=None, **kwargs):
        self.template_path = template_path
        self.static_path = static_path
        self.url = url or ('https' if certfile else 'http') + '://localhost:{port}?index={index}'
        self.refresh = int(refresh) if refresh else 0
        if certfile:
            self.ssl_ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            self.ssl_ctx.check_hostname = False
            self.ssl_ctx.verify_mode = ssl.CERT_NONE
            self.ssl_ctx.load_cert_chain(certfile, keyfile=keyfile)
        else:
            self.ssl_ctx = None

        # Disable all the output of the tornado server to avoid messing up with Fuzzinator's messages.
        hn = logging.NullHandler()
        hn.setLevel(logging.DEBUG)
        logging.getLogger('tornado.access').addHandler(hn)
        logging.getLogger('tornado.access').propagate = False

    def __call__(self, fuzzer_class):
        decorator = self

        class DecoratedFuzzer(fuzzer_class):

            def __init__(self, **kwargs):
                signature(self.__init__).bind(**kwargs)
                super().__init__(**kwargs)
                self.index = 0
                self.test = None
                self.__port = None
                self.__thread = None
                self.__asyncio_loop = None
                self.__ioloop = None
            __init__.__signature__ = signature(fuzzer_class.__init__)

            def _url(self):
                return decorator.url.format(port=self.__port, index=self.index)

            def _service(self):
                return '{scheme}://localhost:{port}'.format(scheme='https' if decorator.ssl_ctx else 'http', port=self.__port)

            def __call__(self, *, index):
                if index != 0 and self.test is None:
                    return None

                return self._url()

            def __enter__(self):
                fuzzer = super().__call__

                def start_tornado():
                    # Create a new asyncio event loop, set it as current, and wrap it in Tornado's IOLoop.
                    self.__asyncio_loop = asyncio.new_event_loop()  # save asyncio event loop so that we can cancel its tasks when shutting down
                    asyncio.set_event_loop(self.__asyncio_loop)
                    self.__ioloop = IOLoop.current()  # save the Tornado-wrapped event loop so that we can stop it when shutting down

                    # Set up the web service (application).
                    handlers = [(r'/', self.MainHandler, dict(wrapper=self, fuzzer=fuzzer))]
                    if decorator.template_path:
                        handlers += [(r'/(.+)', self.TemplateHandler, {})]

                    app = Application(handlers,
                                      template_path=decorator.template_path,
                                      static_path=decorator.static_path,
                                      debug=True)
                    app.listen(self.__port, ssl_options=decorator.ssl_ctx)

                    # Run the event loop and the application within.
                    logger.debug('Starting Tornado server at %s', self._service())
                    self.__ioloop.start()  # block here until even loop is stopped
                    self.__ioloop.close(all_fds=True)  # release port after event loop is stopped
                    logger.debug('Stopped Tornado server at %s', self._service())

                # Call decorated fuzzer's __enter__.
                super().__enter__()

                # Start Tornado in a separate thread.
                _, self.__port = bind_unused_port()  # get random available port before starting the thread, because we cannot be sure when the thread will actually start and __call__ may need it sooner
                self.__thread = threading.Thread(target=start_tornado)  # save the thread so that we can join it when shutting down
                self.__thread.start()

                return self

            def __exit__(self, *exc):
                def stop_tornado():
                    # (Ask to) cancel all pending tasks of the underlying asyncio event loop. Cancellation actually happens in a next iteration of the loop.
                    for task in asyncio_all_tasks(self.__asyncio_loop):  # this is to avoid harmless(?) "ERROR:asyncio:Task was destroyed but it is pending!" messages
                        task.cancel()
                    # Ask to stop the event loop (after the cancellations happen).
                    self.__ioloop.add_callback(self.__ioloop.stop)

                # Call decorated fuzzer's __exit__.
                suppress = super().__exit__(*exc)

                # Stop the thread of Tornado and wait until it terminates.
                logger.debug('Stopping Tornado server at %s', self._service())
                self.__ioloop.add_callback(stop_tornado)
                self.__thread.join()

                return suppress

            class MainHandler(RequestHandler):

                def __init__(self, application, request, wrapper, fuzzer):
                    super().__init__(application, request)
                    self.wrapper = wrapper
                    self.fuzzer = fuzzer

                def data_received(self, chunk):
                    pass

                def get(self):
                    try:
                        self.wrapper.test = self.fuzzer(index=self.wrapper.index)

                        if self.wrapper.test is not None:
                            self.wrapper.index += 1
                            if decorator.refresh > 0:
                                self.set_header('Refresh', '{timeout}; url={url}'
                                                .format(timeout=decorator.refresh,
                                                        url=self.wrapper._url()))
                            test = self.wrapper.test
                            if not isinstance(test, (str, bytes, dict)):
                                test = str(test)
                            self.write(test)
                    except Exception as e:
                        logger.warning('Unhandled exception in TornadoDecorator.', exc_info=e)

            class TemplateHandler(RequestHandler):

                def get(self, page):
                    try:
                        self.render(page + '.html')
                    except FileNotFoundError:
                        logger.debug('%s not found', page)
                        self.send_error(404)
                    except Exception as e:
                        logger.debug('Exception while rendering %s', page, exc_info=e)
                        self.send_error(500)

        return DecoratedFuzzer
