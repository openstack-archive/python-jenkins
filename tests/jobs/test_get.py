import json
from mock import patch

import jenkins
from tests.helper import build_response_mock
from tests.jobs.base import JenkinsGetJobsTestBase


class JenkinsGetJobsTest(JenkinsGetJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jobs = {
            u'url': u'http://your_url_here/job/my_job/',
            u'color': u'blue',
            u'name': u'my_job',
        }
        job_info_to_return = {u'jobs': jobs}
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        job_info = self.j.get_jobs(folder_depth_per_request=1)

        jobs[u'fullname'] = jobs[u'name']
        self.assertEqual(job_info, [jobs])
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('api/json?tree=jobs[url,color,name,jobs]'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_folders_simple(self, jenkins_mock):
        jenkins_mock.side_effect = map(json.dumps, self.jobs_in_folder)

        jobs_info = self.j.get_jobs()

        expected_fullnames = [
            u"my_job1", u"my_folder1", u"my_job2"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_folders_additional_level(self, jenkins_mock):
        jenkins_mock.side_effect = map(json.dumps, self.jobs_in_folder)

        jobs_info = self.j.get_jobs(folder_depth=1)

        expected_fullnames = [
            u"my_job1", u"my_folder1", u"my_job2",
            u"my_folder1/my_job3", u"my_folder1/my_job4"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_view_jobs(self, jenkins_mock):
        view_jobs_to_return = {
            u'jobs': [{
                u'name': u'community.all',
                u'url': u'http://your_url_here',
                u'color': u'grey'
            }, {
                u'name': u'community.first',
                u'url': u'http://your_url_here',
                u'color': u'red'
            }]
        }
        jenkins_mock.return_value = json.dumps(view_jobs_to_return)

        view_jobs = self.j.get_jobs(view_name=u'Test View')

        self.assertEqual(view_jobs[0][u'color'], u'grey')
        self.assertEqual(view_jobs[1][u'name'], u'community.first')
        self.assertEqual(view_jobs[1][u'name'], view_jobs[1][u'fullname'])
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url(
                'view/Test%20View/api/json?tree=jobs[url,color,name]'
            ))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_view_jobs_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_jobs(view_name=u'Test View')

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url(
                'view/Test%20View/api/json?tree=jobs[url,color,name]'
            ))
        self.assertEqual(
            str(context_manager.exception),
            'view[Test View] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_view_jobs_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_jobs(view_name=u'Test View')

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url(
                'view/Test%20View/api/json?tree=jobs[url,color,name]'
            ))
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for view[Test View]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_get_view_jobs_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_jobs(view_name=u'Test View')

        self.assertEqual(
            session_send_mock.call_args_list[1][0][1].url,
            self.make_url(
                'view/Test%20View/api/json?tree=jobs[url,color,name]'
            ))
        self.assertEqual(
            str(context_manager.exception),
            'view[Test View] does not exist')
