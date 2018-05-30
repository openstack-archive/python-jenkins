import sys

from testscenarios import TestWithScenarios

import jenkins

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class JenkinsTestBase(TestWithScenarios, unittest.TestCase):

    crumb_data = {
        "crumb": "dab177f483b3dd93483ef6716d8e792d",
        "crumbRequestField": ".crumb",
    }

    scenarios = [
        ('base_url1', dict(base_url='http://example.com')),
        ('base_url2', dict(base_url='http://example.com/jenkins'))
    ]

    def setUp(self):
        super(JenkinsTestBase, self).setUp()
        # TODO(darragh) would be useful if this could be mocked
        jenkins.requests_kerberos = None

        self.j = jenkins.Jenkins(self.base_url, 'test', 'test')

    def make_url(self, path):
        return u'{0}/{1}'.format(self.base_url, path)

    def _check_requests(self, requests):

        for req in requests:
            req[0][0].prepare()
