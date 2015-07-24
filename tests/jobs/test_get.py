import json
from mock import patch

import jenkins
from tests.jobs.base import JenkinsJobsTestBase


class JenkinsGetJobsTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jobs = {
            u'url': u'http://your_url_here/job/my_job/',
            u'color': u'blue',
            u'name': u'my_job',
        }
        job_info_to_return = {u'jobs': jobs}
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        job_info = self.j.get_jobs()

        self.assertEqual(job_info, jobs)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/api/json')
        self._check_requests(jenkins_mock.call_args_list)
