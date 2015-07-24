import json
import socket

from mock import patch
import six

import jenkins
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


def get_mock_urlopen_return_value(a_dict=None):
    if a_dict is None:
        a_dict = {}
    return six.BytesIO(json.dumps(a_dict).encode('utf-8'))


class JenkinsConstructorTest(JenkinsTestBase):

    def test_url_with_trailing_slash(self):
        self.assertEqual(self.j.server, 'http://example.com/')
        self.assertEqual(self.j.auth, b'Basic dGVzdDp0ZXN0')
        self.assertEqual(self.j.crumb, None)

    def test_url_without_trailing_slash(self):
        j = jenkins.Jenkins('http://example.com', 'test', 'test')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic dGVzdDp0ZXN0')
        self.assertEqual(j.crumb, None)

    def test_without_user_or_password(self):
        j = jenkins.Jenkins('http://example.com')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, None)
        self.assertEqual(j.crumb, None)

    def test_unicode_password(self):
        j = jenkins.Jenkins('http://example.com',
                            six.u('nonascii'),
                            six.u('\xe9\u20ac'))
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic bm9uYXNjaWk6w6nigqw=')
        self.assertEqual(j.crumb, None)

    def test_long_user_or_password(self):
        long_str = 'a' * 60
        long_str_b64 = 'YWFh' * 20

        j = jenkins.Jenkins('http://example.com', long_str, long_str)

        self.assertNotIn(b"\n", j.auth)
        self.assertEqual(j.auth.decode('utf-8'), 'Basic %s' % (
            long_str_b64 + 'Om' + long_str_b64[2:] + 'YQ=='))

    def test_default_timeout(self):
        j = jenkins.Jenkins('http://example.com')
        self.assertEqual(j.timeout, socket._GLOBAL_DEFAULT_TIMEOUT)

    def test_custom_timeout(self):
        j = jenkins.Jenkins('http://example.com', timeout=300)
        self.assertEqual(j.timeout, 300)


class JenkinsMaybeAddCrumbTest(JenkinsTestBase):

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_simple(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(
            404, reason="Not Found")
        request = jenkins.requests.Request('http://example.com/job/TestJob')

        self.j.maybe_add_crumb(request)

        self.assertEqual(
            session_send_mock.call_args[0][1].url,
            'http://example.com/crumbIssuer/api/json')
        self.assertFalse(self.j.crumb)
        self.assertFalse('.crumb' in request.headers)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_with_data(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(
            200, self.crumb_data)
        request = jenkins.requests.Request('GET', 'http://example.com/job/TestJob')

        self.j.maybe_add_crumb(request)

        self.assertEqual(
            session_send_mock.call_args[0][1].url,
            'http://example.com/crumbIssuer/api/json')
        self.assertEqual(self.j.crumb, self.crumb_data)
        self.assertEqual(request.headers['.crumb'], self.crumb_data['crumb'])

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_empty_response(self, jenkins_mock):
        "Don't try to create crumb header from an empty response"
        jenkins_mock.side_effect = jenkins.EmptyResponseException("empty response")
        request = jenkins.requests.Request('GET', 'http://example.com/job/TestJob')

        self.j.maybe_add_crumb(request)

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            'http://example.com/crumbIssuer/api/json')
        self.assertFalse(self.j.crumb)
        self.assertFalse('.crumb' in request.headers)
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsOpenTest(JenkinsTestBase):

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_simple(self, session_send_mock):
        data = {'foo': 'bar'}
        session_send_mock.side_effect = iter([
            build_response_mock(200, self.crumb_data),
            build_response_mock(200, data),
        ])
        request = jenkins.requests.Request('GET', 'http://example.com/job/TestJob')

        response = self.j.jenkins_open(request)

        self.assertEqual(
            session_send_mock.call_args[0][1].url,
            'http://example.com/job/TestJob')
        self.assertEqual(response, json.dumps(data))
        self.assertEqual(self.j.crumb, self.crumb_data)
        self.assertEqual(request.headers['.crumb'], self.crumb_data['crumb'])

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_response_403(self, session_send_mock):
        request = jenkins.requests.Request('GET', 'http://example.com/job/TestJob')
        session_send_mock.return_value = build_response_mock(
            401, reason="basic auth failed")

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request. Possibly authentication failed [401]: '
            'basic auth failed')
        self.assertEqual(
            session_send_mock.call_args[0][1].url,
            'http://example.com/job/TestJob')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_response_404(self, session_send_mock):
        request = jenkins.requests.Request('GET', 'http://example.com/job/TestJob')
        session_send_mock.return_value = build_response_mock(
            404, reason="basic auth failed")

        with self.assertRaises(jenkins.NotFoundException) as context_manager:
            self.j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            'Requested item could not be found')
        self.assertEqual(
            session_send_mock.call_args[0][1].url,
            'http://example.com/job/TestJob')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_empty_response(self, session_send_mock):
        request = jenkins.requests.Request('GET', 'http://example.com/job/TestJob')
        session_send_mock.return_value = build_response_mock(
            401, reason="basic auth failed")

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.jenkins_open(request, False)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request. Possibly authentication failed [401]: '
            'basic auth failed')
        self.assertEqual(
            session_send_mock.call_args[0][1].url,
            'http://example.com/job/TestJob')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_response_501(self, session_send_mock):
        request = jenkins.requests.Request('GET', 'http://example.com/job/TestJob')
        session_send_mock.return_value = build_response_mock(
            501, reason="Not implemented")

        with self.assertRaises(jenkins.req_exc.HTTPError) as context_manager:
            self.j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            '501 Server Error: Not implemented')
        self.assertEqual(
            session_send_mock.call_args[0][1].url,
            'http://example.com/job/TestJob')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_timeout(self, session_send_mock):
        session_send_mock.side_effect = jenkins.URLError(
            reason="timed out")
        j = jenkins.Jenkins('http://example.com/', 'test', 'test', timeout=1)
        request = jenkins.requests.Request('GET', 'http://example.com/job/TestJob')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request: timed out')
        self.assertEqual(
            session_send_mock.call_args[0][1].url,
            'http://example.com/job/TestJob')
