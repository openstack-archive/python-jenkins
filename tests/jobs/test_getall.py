import json
from mock import patch

import jenkins
from tests.jobs.base import JenkinsGetJobsTestBase


class JenkinsGetAllJobsTest(JenkinsGetJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = map(json.dumps, self.jobs_in_folder)

        jobs_info = self.j.get_all_jobs()

        expected_fullnames = [
            u"my_job1", u"my_folder1", u"my_job2",
            u"my_folder1/my_job3", u"my_folder1/my_job4"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

        expected_request_urls = [
            self.make_url('api/json'),
            self.make_url('job/my_folder1/api/json')
        ]
        self.assertEqual(expected_request_urls,
                         self.got_request_urls(jenkins_mock))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_multi_level(self, jenkins_mock):
        jenkins_mock.side_effect = map(
            json.dumps, self.jobs_in_multiple_folders)

        jobs_info = self.j.get_all_jobs()

        expected_fullnames = [
            u"my_job1", u"my_folder1", u"my_job2", u"my_folder1/my_folder2",
            u"my_folder1/my_job3", u"my_folder1/my_job4",
            u"my_folder1/my_folder2/my_job1", u"my_folder1/my_folder2/my_job2"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)
        # multiple jobs with same name
        self.assertEqual(2, len([True
                                 for job in jobs_info
                                 if job['name'] == u"my_job1"]))

        expected_request_urls = [
            self.make_url('api/json'),
            self.make_url('job/my_folder1/api/json'),
            self.make_url('job/my_folder1/job/my_folder2/api/json')
        ]
        self.assertEqual(expected_request_urls,
                         self.got_request_urls(jenkins_mock))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_folders_depth(self, jenkins_mock):
        jenkins_mock.side_effect = map(
            json.dumps, self.jobs_in_multiple_folders)

        jobs_info = self.j.get_all_jobs(folder_depth=1)

        expected_fullnames = [
            u"my_job1", u"my_folder1", u"my_job2", u"my_folder1/my_folder2",
            u"my_folder1/my_job3", u"my_folder1/my_job4"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

        expected_request_urls = [
            self.make_url('api/json'),
            self.make_url('job/my_folder1/api/json')
        ]
        self.assertEqual(expected_request_urls,
                         self.got_request_urls(jenkins_mock))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_unsafe_chars(self, jenkins_mock):
        jenkins_mock.side_effect = map(
            json.dumps, self.jobs_in_unsafe_name_folders)

        jobs_info = self.j.get_all_jobs()

        expected_fullnames = [
            u"my_job1", u"my_folder1", u"my_job2", u"my_folder1/my spaced folder",
            u"my_folder1/my_job3", u"my_folder1/my_job4",
            u"my_folder1/my spaced folder/my job 5"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

        expected_request_urls = [
            self.make_url('api/json'),
            self.make_url('job/my_folder1/api/json'),
            self.make_url('job/my_folder1/job/my%20spaced%20folder/api/json')
        ]
        self.assertEqual(expected_request_urls,
                         self.got_request_urls(jenkins_mock))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_folder_named_job(self, jenkins_mock):
        jenkins_mock.side_effect = map(
            json.dumps, self.jobs_in_folder_named_job)

        jobs_info = self.j.get_all_jobs()

        expected_fullnames = [u"job", u"job/my_job"]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

        expected_request_urls = [
            self.make_url('api/json'),
            self.make_url('job/job/api/json'),
        ]
        self.assertEqual(expected_request_urls,
                         self.got_request_urls(jenkins_mock))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_deep_query(self, jenkins_mock):
        jenkins_mock.side_effect = map(
            json.dumps, self.jobs_in_folder_deep_query)

        jobs_info = self.j.get_all_jobs()

        expected_fullnames = [
            u"top_folder",
            u"top_folder/middle_folder",
            u"top_folder/middle_folder/bottom_folder",
            u"top_folder/middle_folder/bottom_folder/my_job1",
            u"top_folder/middle_folder/bottom_folder/my_job2"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

        expected_request_urls = [
            self.make_url('api/json'),
            self.make_url('job/top_folder/job/middle_folder/job/bottom_folder/api/json')
        ]
        self.assertEqual(expected_request_urls,
                         self.got_request_urls(jenkins_mock))
