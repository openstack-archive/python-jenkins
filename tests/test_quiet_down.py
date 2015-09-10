import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase


class JenkinsPrepareForShutdownTest(JenkinsTestBase):
    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_success(self, jenkins_mock):
        job_info_to_return = {
            "quietingDown": True,
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        self.j.prepare_for_shutdown()

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            u'http://example.com/quietDown')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            u'http://example.com/api/json')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_fail(self, jenkins_mock):
        job_info_to_return = {
            "quietingDown": False,
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.prepare_for_shutdown()

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            u'http://example.com/quietDown')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            u'http://example.com/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'quiet down failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_http_fail(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/quietDown',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)

        with self.assertRaises(jenkins.HTTPError):
            self.j.prepare_for_shutdown()

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/quietDown')
        self._check_requests(jenkins_mock.call_args_list)
