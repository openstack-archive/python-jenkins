import functools
import logging
from multiprocessing import Process

from six.moves import socketserver


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestsTimeoutException(Exception):
    pass


def time_limit(seconds, func, *args, **kwargs):
    def capture_exceptions(func, *args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            logger.info("Running function '%s' resulted in exception '%s' "
                        "with message: '%s'" % (func.__name__,
                                                e.__class__.__name__,
                                                e.message))
            raise
        else:
            logger.info("Running function '%s' finished with result '%s' " %
                        (func.__name__, result))
            return 0

    # although creating a separate process is expensive it's the only way to
    # ensure cross platform that we can cleanly terminate after timeout
    p = Process(target=functools.partial(capture_exceptions, func),
                args=args, kwargs=kwargs)
    p.start()
    p.join(seconds)
    p.terminate()
    if p.exitcode is None:
        logger.info("Running function '%s' did not finish" % func.__name__)
        raise TestsTimeoutException
    else:
        logger.info("Running function '%s' finished with exit code '%s' " %
                    (func.__name__, p.exitcode))


class NullServer(socketserver.TCPServer):

    request_queue_size = 1

    def __init__(self, server_address, *args, **kwargs):
        # TCPServer is old style in python 2.x so cannot use
        # super() correctly, explicitly call __init__.

        # simply init'ing is sufficient to open the port, which
        # with the server not started creates a black hole server
        socketserver.TCPServer.__init__(
            self, server_address, socketserver.BaseRequestHandler,
            *args, **kwargs)
