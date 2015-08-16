import sys

from six.moves.urllib.request import build_opener

import jenkins

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class JenkinsTestBase(unittest.TestCase):

    crumb_data = {
        "crumb": "dab177f483b3dd93483ef6716d8e792d",
        "crumbRequestField": ".crumb",
    }

    def setUp(self):
        super(JenkinsTestBase, self).setUp()
        self.opener = build_opener()

        self.j = jenkins.Jenkins('http://example.com/', 'test', 'test')

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
