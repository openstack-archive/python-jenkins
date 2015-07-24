import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


class JenkinsInfoTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info(self, jenkins_mock):
        job_info_to_return = {
            u'jobs': {
                u'url': u'http://your_url_here/job/my_job/',
                u'color': u'blue',
                u'name': u'my_job',
            }
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_info()

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/api/json')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_get_info__HTTPError(self, session_send_mock):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),        # crumb
            build_response_mock(499, reason="Unhandled Error"),  # request
        ])

        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            j.get_info()
        self.assertEqual(
            session_send_mock.call_args_list[1][0][1].url,
            u'http://example.com/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__BadStatusLine(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.BadStatusLine('not a valid status line')
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__ValueError(self, jenkins_mock):
        jenkins_mock.return_value = 'not valid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__empty_response(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.JenkinsException(
            "Error communicating with server[http://example.com/]: "
            "empty response")
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]: '
            'empty response')
        self._check_requests(jenkins_mock.call_args_list)
