import sys

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
        self.j = jenkins.Jenkins('http://example.com/', 'test', 'test')

    def _check_requests(self, requests):

        for req in requests:
            req[0][0].prepare()
