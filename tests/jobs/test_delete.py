import json
from mock import patch

import jenkins
from tests.jobs.base import JenkinsJobsTestBase


class JenkinsDeleteJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]

        self.j.delete_job(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/Test%20Job/doDelete')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.delete_job(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/doDelete')
        self.assertEqual(
            str(context_manager.exception),
            'delete[TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)
