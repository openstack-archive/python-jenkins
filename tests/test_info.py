import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


class JenkinsInfoTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        job_info_to_return = {
            u'jobs': {
                u'url': u'http://your_url_here/job/my_job/',
                u'color': u'blue',
                u'name': u'my_job',
            }
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        job_info = self.j.get_info()

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('api/json'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),        # crumb
            build_response_mock(499, reason="Unhandled Error"),  # request
        ])

        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_info()
        self.assertEqual(
            session_send_mock.call_args_list[1][0][1].url,
            self.make_url('api/json'))
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}]'.format(self.make_url('')))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_BadStatusLine(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.BadStatusLine('not a valid status line')

        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('api/json'))
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}]'.format(self.make_url('')))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'not valid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('api/json'))
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for server[{0}]'.format(self.make_url('')))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_empty_response(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.JenkinsException(
            "Error communicating with server[{0}]: empty response".
            format(self.make_url('')))

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('api/json'))
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}]: '
            'empty response'.format(self.make_url('')))
        self._check_requests(jenkins_mock.call_args_list)
