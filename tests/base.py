import sys

import mock
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

        self.request_kerberos_module_patcher = mock.patch(
            'jenkins.requests_kerberos', None)
        self.request_kerberos_module_patcher.start()

        self.j = jenkins.Jenkins(self.base_url, 'test', 'test')

    def tearDown(self):

        self.request_kerberos_module_patcher.stop()

    def make_url(self, path):
        return u'{0}/{1}'.format(self.base_url, path)

    def _check_requests(self, requests):

        for req in requests:
            req[0][0].prepare()

    def got_request_urls(self, mock):
        return [
            call[0][0].url.split('?')[0]
            for call in mock.call_args_list
        ]
