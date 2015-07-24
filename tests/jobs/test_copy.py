import json
from mock import patch

import jenkins
from tests.jobs.base import JenkinsJobsTestBase


class JenkinsCopyJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
        ]

        self.j.copy_job(u'Test Job', u'Test Job_2')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/createItem'
            '?name=Test%20Job_2&mode=copy&from=Test%20Job')
        self.assertTrue(self.j.job_exists('Test Job_2'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.copy_job(u'TestJob', u'TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/createItem'
            '?name=TestJob_2&mode=copy&from=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)
