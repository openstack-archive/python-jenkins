import json
from multiprocessing import Process

from mock import Mock
import requests
from six.moves import socketserver


class TestsTimeoutException(Exception):
    pass


def time_limit(seconds, func, *args, **kwargs):
    # although creating a separate process is expensive it's the only way to
    # ensure cross platform that we can cleanly terminate after timeout
    p = Process(target=func, args=args, kwargs=kwargs)
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


def build_response_mock(status_code, json_body=None, headers=None, **kwargs):
    real_response = requests.Response()
    real_response.status_code = status_code

    text = None
    if json_body is not None:
        text = json.dumps(json_body).encode('utf-8')
        if headers is not {}:
            real_response.headers['content-length'] = len(text)

    if headers is not None:
        for k, v in headers.items():
            real_response.headers[k] = v

    for k, v in kwargs.items():
        setattr(real_response, k, v)

    response = Mock(wraps=real_response, autospec=True)
    if text:
        response.text = text

    # for some reason, wraps cannot handle attributes which are dicts
    # and accessed by key
    response.headers = real_response.headers

    return response
