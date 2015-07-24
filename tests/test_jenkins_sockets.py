import sys

import jenkins
from tests.helper import NullServer
from tests.helper import TestsTimeoutException
from tests.helper import time_limit

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class JenkinsRequestTimeoutTests(unittest.TestCase):

    def setUp(self):
        super(JenkinsRequestTimeoutTests, self).setUp()
        self.server = NullServer(("127.0.0.1", 0))

    def test_jenkins_open_timeout(self):
        j = jenkins.Jenkins("http://%s:%s" % self.server.server_address,
                            None, None, timeout=0.1)
        request = jenkins.requests.Request('GET', 'http://%s:%s/job/TestJob' %
                                           self.server.server_address)

        # assert our request times out when no response
        with self.assertRaises(jenkins.TimeoutException):
            j.jenkins_open(request, add_crumb=False)

    def test_jenkins_open_no_timeout(self):
        j = jenkins.Jenkins("http://%s:%s" % self.server.server_address,
                            None, None)
        request = jenkins.requests.Request('GET', 'http://%s:%s/job/TestJob' %
                                           self.server.server_address)

        # assert we don't timeout quickly like previous test when
        # no timeout defined.
        with self.assertRaises(TestsTimeoutException):
            time_limit(0.5, j.jenkins_open, request, add_crumb=False)
