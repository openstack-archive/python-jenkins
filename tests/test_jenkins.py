import json
import socket

from mock import patch, Mock
import six
from six.moves.urllib.error import HTTPError

import jenkins
from tests.base import JenkinsTestBase


def get_mock_urlopen_return_value(a_dict=None):
    if a_dict is None:
        a_dict = {}
    return six.BytesIO(json.dumps(a_dict).encode('utf-8'))


class JenkinsTest(JenkinsTestBase):

    def test_constructor_url_with_trailing_slash(self):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic dGVzdDp0ZXN0')
        self.assertEqual(j.crumb, None)

    def test_constructor_url_without_trailing_slash(self):
        j = jenkins.Jenkins('http://example.com', 'test', 'test')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic dGVzdDp0ZXN0')
        self.assertEqual(j.crumb, None)

    def test_constructor_without_user_or_password(self):
        j = jenkins.Jenkins('http://example.com')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, None)
        self.assertEqual(j.crumb, None)

    def test_constructor_unicode_password(self):
        j = jenkins.Jenkins('http://example.com',
                            six.u('nonascii'),
                            six.u('\xe9\u20ac'))
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic bm9uYXNjaWk6w6nigqw=')
        self.assertEqual(j.crumb, None)

    def test_constructor_long_user_or_password(self):
        long_str = 'a' * 60
        long_str_b64 = 'YWFh' * 20

        j = jenkins.Jenkins('http://example.com', long_str, long_str)

        self.assertNotIn(b"\n", j.auth)
        self.assertEqual(j.auth.decode('utf-8'), 'Basic %s' % (
            long_str_b64 + 'Om' + long_str_b64[2:] + 'YQ=='))

    def test_constructor_default_timeout(self):
        j = jenkins.Jenkins('http://example.com')
        self.assertEqual(j.timeout, socket._GLOBAL_DEFAULT_TIMEOUT)

    def test_constructor_custom_timeout(self):
        j = jenkins.Jenkins('http://example.com', timeout=300)
        self.assertEqual(j.timeout, 300)


class JenkinsMaybeAddCrumbTest(JenkinsTestBase):

    @patch('jenkins.urlopen')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        j.maybe_add_crumb(request)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/crumbIssuer/api/json')
        self.assertFalse(j.crumb)
        self.assertFalse('.crumb' in request.headers)
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_with_data(self, jenkins_mock):
        crumb_data = {
            "crumb": "dab177f483b3dd93483ef6716d8e792d",
            "crumbRequestField": ".crumb",
        }
        jenkins_mock.return_value = get_mock_urlopen_return_value(crumb_data)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        j.maybe_add_crumb(request)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/crumbIssuer/api/json')
        self.assertEqual(j.crumb, crumb_data)
        self.assertEqual(request.headers['.crumb'], crumb_data['crumb'])
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_empty_response(self, jenkins_mock):
        "Don't try to create crumb header from an empty response"
        jenkins_mock.side_effect = jenkins.EmptyResponseException("empty response")
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        j.maybe_add_crumb(request)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/crumbIssuer/api/json')
        self.assertFalse(j.crumb)
        self.assertFalse('.crumb' in request.headers)
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsOpenTest(JenkinsTestBase):

    @patch('jenkins.urlopen')
    def test_simple(self, jenkins_mock):
        crumb_data = {
            "crumb": "dab177f483b3dd93483ef6716d8e792d",
            "crumbRequestField": ".crumb",
        }
        data = {'foo': 'bar'}
        jenkins_mock.side_effect = [
            get_mock_urlopen_return_value(crumb_data),
            get_mock_urlopen_return_value(data),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        response = j.jenkins_open(request)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/job/TestJob')
        self.assertEqual(response, json.dumps(data))
        self.assertEqual(j.crumb, crumb_data)
        self.assertEqual(request.headers['.crumb'], crumb_data['crumb'])
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_response_403(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request. Possibly authentication failed [401]: '
            'basic auth failed')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/job/TestJob')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_response_404(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=404,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        with self.assertRaises(jenkins.NotFoundException) as context_manager:
            j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            'Requested item could not be found')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/job/TestJob')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_empty_response(self, jenkins_mock):
        jenkins_mock.return_value = Mock(**{'read.return_value': None})

        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.jenkins_open(request, False)
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]: '
            'empty response')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/job/TestJob')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_response_501(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=501,
            msg="Not implemented",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        with self.assertRaises(HTTPError) as context_manager:
            j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            'HTTP Error 501: Not implemented')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/job/TestJob')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_timeout(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.URLError(
            reason="timed out")
        j = jenkins.Jenkins('http://example.com/', 'test', 'test', timeout=1)
        request = jenkins.Request('http://example.com/job/TestJob')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request: timed out')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/job/TestJob')
        self._check_requests(jenkins_mock.call_args_list)
