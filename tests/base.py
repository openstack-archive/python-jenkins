import sys

from six.moves.urllib.request import build_opener

import jenkins

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class _AddUrlPathMeta(type):
    """Custom metaclass to dynamically add additional url tests

    Using a custom metaclass to extend the tests to exercise all the
    API calls using a different jenkins server url, will ensure that
    as tests are added, can continue to check variations.
    """

    ignore_class_suffixes = [
        'Base',
        'Scenarios',
        'UrlPathTest'
    ]

    def __new__(cls, name, bases, nmspc):
        cls = super(_AddUrlPathMeta, cls).__new__(cls, name, bases, nmspc)
        if not any(name.endswith(suffix)
                   for suffix in _AddUrlPathMeta.ignore_class_suffixes):
            new_bases = [cls]
            new_bases += bases
            new_class = type(name.replace("Test", "UrlPathTest"),
                             tuple(new_bases),
                             {'base_url': 'http://example.com/jenkins'})
            new_class.__module__ = cls.__module__
            setattr(sys.modules[cls.__module__], new_class.__name__, new_class)

        return cls


class JenkinsTestBase(unittest.TestCase):
    __metaclass__ = _AddUrlPathMeta

    crumb_data = {
        "crumb": "dab177f483b3dd93483ef6716d8e792d",
        "crumbRequestField": ".crumb",
    }

    base_url = 'http://example.com'

    def setUp(self):
        super(JenkinsTestBase, self).setUp()
        self.opener = build_opener()

        self.j = jenkins.Jenkins(self.base_url, 'test', 'test')

    def _check_requests(self, requests):

        for req in requests:
            self._check_request(req[0][0])

    def _check_request(self, request):

        # taken from opener.open() in request
        # attribute request.type is only set automatically for python 3
        # requests, must use request.get_type() for python 2.7
        protocol = request.type or request.get_type()

        # check that building the request doesn't throw any exception
        meth_name = protocol + "_request"
        for processor in self.opener.process_request.get(protocol, []):
            meth = getattr(processor, meth_name)
            request = meth(request)
