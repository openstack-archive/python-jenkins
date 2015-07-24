import json
from mock import patch

import jenkins
from tests.jobs.base import JenkinsJobsTestBase


class JenkinsEnableJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]

        self.j.enable_job(u'TestJob')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/TestJob/enable')
        self.assertTrue(self.j.job_exists('TestJob'))
        self._check_requests(jenkins_mock.call_args_list)
