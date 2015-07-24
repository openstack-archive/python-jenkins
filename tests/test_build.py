import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


class JenkinsBuildConsoleTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.return_value = "build console output..."

        build_info = self.j.get_build_console_output(u'Test Job', number=52)

        self.assertEqual(build_info, jenkins_mock.return_value)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/Test%20Job/52/consoleText')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'

        console_output = self.j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(console_output, jenkins_mock.return_value)
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send')
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(
            session_send_mock.call_args_list[1][0][0].url,
            u'http://example.com/job/TestJob/52/consoleText')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')


class JenkinsBuildInfoTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        build_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(build_info_to_return)

        build_info = self.j.get_build_info(u'Test Job', number=52)

        self.assertEqual(build_info, build_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/Test%20Job/52/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for job[TestJob] number[52]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')


class JenkinsStopBuildTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        self.j.stop_build(u'Test Job', number=52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/Test%20Job/52/stop')
        self._check_requests(jenkins_mock.call_args_list)
