# Copyright (c) 2016 Renata Hodovan, Akos Kiss.
#
# Licensed under the BSD 3-Clause License
# <LICENSE.md or https://opensource.org/licenses/BSD-3-Clause>.
# This file may not be copied, modified, or distributed except
# according to those terms.

import logging
import threading

from inspect import isclass, isroutine
from tornado.ioloop import IOLoop
from tornado.template import Template
from tornado.web import Application, RequestHandler

logger = logging.getLogger(__name__)


class TornadoDecorator(object):
    """
    Decorator for fuzzers to transport generated content through http. The
    decorator starts a Tornado server at the start of the fuzz job and returns
    a http url as test input. The SUT is expected to access the returned url and
    the decorated fuzzer is invoked on every GET access to that url. The
    response to the GET contains the generated test input prepended by a html
    meta tag to force continuous reloads in the SUT (or a 'window.close()'
    javascript content to force stopping the SUT if the decorated fuzzer cannot
    generate more tests). Useful for transporting fuzz tests to browser SUTs.

    Mandatory parameter of the fuzzer decorator:
      - 'port': first port to start binding the started http server to (keeps
        incrementing until a free port is found).

    Example configuration snippet:
    [sut.foo]
    # assuming that foo expects a http url as input, which it tries to access
    # afterwards

    [fuzz.foo-with-bar-over-http]
    sut=sut.foo
    #fuzzer=...
    fuzzer.decorate(0)=fuzzinator.fuzzer.TornadoDecorator
    batch=5

    [fuzz.foo-with-bar-over-http.fuzzer.decorate(0)]
    port=8000
    """

    def __init__(self, port, **kwargs):
        self.port = int(port)

        # Disable all the output of the tornado server to avoid messing up with Fuzzinator's messages.
        hn = logging.NullHandler()
        hn.setLevel(logging.DEBUG)
        logging.getLogger("tornado.access").addHandler(hn)
        logging.getLogger("tornado.access").propagate = False

    def __call__(self, callable):
        ancestor = object if isroutine(callable) else callable

        class Inherited(ancestor):
            decorator = self

            def __init__(self, *args, **kwargs):
                if hasattr(ancestor, '__init__'):
                    super(Inherited, self).__init__(*args, **kwargs)
                self.index = 0
                self.test = None
                self.fuzzer_kwargs = dict()
                self.ioloop = None

            def __call__(self, **kwargs):
                # Saving fuzzer args to make them available from the requesthandlers
                # after passing a reference of ourselves.
                if kwargs['index'] != 0 and not self.test:
                    return None

                self.fuzzer_kwargs = kwargs
                return 'http://localhost:{port}?index={index}'.format(port=self.decorator.port, index=self.index)

            def __enter__(self, *args, **kwargs):
                if hasattr(ancestor, '__enter__'):
                    super(Inherited, self).__enter__(*args, **kwargs)

                app = Application([
                    (r'/', self.MainHandler, dict(wrapper=self,
                                                  fuzzer=super(Inherited, self).__call__ if isclass(callable) else callable))
                ])

                while True:
                    try:
                        server = app.listen(self.decorator.port)
                        break
                    except OSError:
                        self.decorator.port += 1

                def ioloop_thread():
                    self.ioloop = IOLoop.current()
                    self.ioloop.start()
                    server.stop()

                logger.debug('Tornado server started.')
                threading.Thread(target=ioloop_thread).start()
                return self

            def __exit__(self, *exc):
                if hasattr(ancestor, '__exit__'):
                    super(Inherited, self).__exit__(*exc)

                self.ioloop.add_callback(self.ioloop.stop)
                logger.debug('Shut down tornado server.')
                return None

            class MainHandler(RequestHandler):

                def __init__(self, application, request, wrapper, fuzzer):
                    RequestHandler.__init__(self, application, request)
                    self.wrapper = wrapper
                    self.fuzzer = fuzzer

                def data_received(self, chunk):
                    pass

                def get(self):
                    content = '<script>window.close();</script>'

                    try:
                        self.wrapper.fuzzer_kwargs['index'] = self.wrapper.index
                        self.wrapper.test = self.fuzzer(**self.wrapper.fuzzer_kwargs)
                        if self.wrapper.test:
                            self.wrapper.index += 1
                            content = Template('<meta http-equiv="refresh" content="1;url=?&{% raw request %}">{% raw test %}'). \
                                generate(request='index={index}'.format(index=self.wrapper.index), test=self.wrapper.test)
                    except Exception as e:
                        logger.warning(e)

                    self.write(content)

        return Inherited
