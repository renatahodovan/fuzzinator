# Copyright (c) 2016-2021 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.rst or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import asyncio
import logging
import socket
import threading

from inspect import isclass, isroutine
from tornado.ioloop import IOLoop
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

    **Optional parameters of the fuzzer decorator:**

      - ``template_path``: Directory containing .html template files. These are
        served from the path / without the .html extension.
      - ``static_path``: Directory from which static files will be served.
        These are served from the path /static/.
      - ``url``: Url template with {port} and {index} placeholders, that will
        be filled in with appropriate values. This is the url that will be
        served for the SUT as the test case.
        (Default: http://localhost:{port}/index={index})
      - ``refresh``: Integer number denoting the time interval (in seconds)
        for the document at the root path (i.e., the test case) to refresh
        itself. Setting it to 0 means no refresh. (Default: 0)

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

    def __init__(self, template_path=None, static_path=None, url=None, refresh=None, **kwargs):
        self.template_path = template_path
        self.static_path = static_path
        self.url = url or 'http://localhost:{port}?index={index}'
        self.refresh = int(refresh) if refresh else 0
        self.port = None

        # Disable all the output of the tornado server to avoid messing up with Fuzzinator's messages.
        hn = logging.NullHandler()
        hn.setLevel(logging.DEBUG)
        logging.getLogger('tornado.access').addHandler(hn)
        logging.getLogger('tornado.access').propagate = False

    def __call__(self, callable):
        ancestor = object if isroutine(callable) else callable
        decorator = self

        class Inherited(ancestor):

            def __init__(self, *args, **kwargs):
                if hasattr(ancestor, '__init__'):
                    super().__init__(*args, **kwargs)
                self.index = 0
                self.test = None
                self.fuzzer_kwargs = dict()
                self.t = None

            def __call__(self, **kwargs):
                # Saving fuzzer args to make them available from the RequestHandlers
                # after passing a reference of ourselves.
                if kwargs['index'] != 0 and self.test is None:
                    return None

                self.fuzzer_kwargs = kwargs
                return decorator.url.format(port=decorator.port, index=self.index)

            def __enter__(self, *args, **kwargs):
                if hasattr(ancestor, '__enter__'):
                    super().__enter__(*args, **kwargs)

                # Get random available port.
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:  # pylint: disable=no-member
                    s.bind(('', 0))
                    decorator.port = s.getsockname()[1]

                handlers = [(r'/', self.MainHandler, dict(wrapper=self, fuzzer=super().__call__ if isclass(callable) else callable))]
                if decorator.template_path:
                    handlers += [(r'/(.+)', self.TemplateHandler, {})]

                app = Application(handlers,
                                  template_path=decorator.template_path,
                                  static_path=decorator.static_path,
                                  debug=True)

                def ioloop_thread():
                    asyncio.set_event_loop(asyncio.new_event_loop())
                    app.listen(decorator.port)
                    IOLoop.current().start()

                logger.debug('Tornado server started.')
                self.t = threading.Thread(target=ioloop_thread)
                self.t.start()
                return self

            def __exit__(self, *exc):
                suppress = False

                if hasattr(ancestor, '__exit__'):
                    suppress = super().__exit__(*exc)

                self.t._stop()
                logger.debug('Shut down tornado server.')
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
                        self.wrapper.fuzzer_kwargs['index'] = self.wrapper.index
                        self.wrapper.test = self.fuzzer(**self.wrapper.fuzzer_kwargs)

                        if self.wrapper.test is not None:
                            self.wrapper.index += 1
                            if decorator.refresh > 0:
                                self.set_header('Refresh', '{timeout}; url={url}'
                                                .format(timeout=decorator.refresh,
                                                        url=decorator.url.format(port=decorator.port,
                                                                                 index=self.wrapper.index)))
                            self.write(str(self.wrapper.test))
                    except Exception as e:
                        logger.warning('Unhandled exception in TornadoDecorator.', exc_info=e)

            class TemplateHandler(RequestHandler):

                def get(self, page):
                    try:
                        self.render(page + '.html')
                    except FileNotFoundError:
                        logger.debug('%s not found', page)
                        self.send_error(404)

        return Inherited
