import functools
from multiprocessing import Process

from six.moves import socketserver


class TestsTimeoutException(Exception):
    pass


def time_limit(seconds, func, *args, **kwargs):
    def capture_exceptions(func, *args, **kwargs):
        try:
            func(*args, **kwargs)
        except Exception as e:
            print("Running function '%s' resulted in exception '%s' with "
                  "message: %s" % (func.__name__, e, e.msg))

    # although creating a separate process is expensive it's the only way to
    # ensure cross platform that we can cleanly terminate after timeout
    p = Process(target=functools.partial(capture_exceptions, func),
                args=args, kwargs=kwargs)
    p.start()
    p.join(seconds)
    p.terminate()
    if p.exitcode is None:
        raise TestsTimeoutException


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
