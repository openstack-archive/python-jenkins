from mock import patch

import jenkins
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


class JenkinsVersionTest(JenkinsTestBase):

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_some_version(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(
            200, headers={'X-Jenkins': 'Version42', 'Content-Length': 0})
        self.assertEqual(self.j.get_version(), 'Version42')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),        # crumb
            build_response_mock(499, reason="Unhandled Error"),  # request
        ])

        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_version()
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}/]'.format(self.base_url))

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_BadStatusLine(self, session_send_mock):
        session_send_mock.side_effect = jenkins.BadStatusLine('not a valid status line')
        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_version()
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}/]'.format(self.base_url))

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_return_empty_response(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(0)
        with self.assertRaises(jenkins.EmptyResponseException) as context_manager:
            self.j.get_version()
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}/]:'
            ' empty response'.format(self.base_url))
