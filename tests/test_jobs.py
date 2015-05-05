import copy
import json
from mock import patch

import jenkins
from tests.base import build_jobs_list_responses
from tests.base import JenkinsTestBase


class JenkinsJobsTestBase(JenkinsTestBase):

    config_xml = """
        <matrix-project>
            <actions/>
            <description>Foo</description>
        </matrix-project>"""


class JenkinsGetJobConfigTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_encodes_job_name(self, jenkins_mock):
        self.j.get_job_config(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/Test%20Job/config.xml')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_encodes_job_name_in_folder(self, jenkins_mock):
        self.j.get_job_config(u'a folder/Test Job')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/a%20folder/job/Test%20Job/config.xml')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsAssertJobExistsTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_job_missing(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.assert_job_exists('NonExistent')
        self.assertEqual(
            str(context_manager.exception),
            'job[NonExistent] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_job_missing_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.assert_job_exists('a Folder/NonExistent')
        self.assertEqual(
            str(context_manager.exception),
            'job[a Folder/NonExistent] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_job_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingJob'}),
        ]
        self.j.assert_job_exists('ExistingJob')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_job_exists_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingJob'}),
        ]
        self.j.assert_job_exists('a Folder/ExistingJob')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsCreateJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            jenkins.NotFoundException(),
            None,
            json.dumps({'name': 'Test Job'}),
        ]

        self.j.create_job(u'Test Job', self.config_xml)

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/createItem?name=Test%20Job')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            jenkins.NotFoundException(),
            None,
            json.dumps({'name': 'Test Job'}),
        ]

        self.j.create_job(u'a Folder/Test Job', self.config_xml)

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/createItem?name=Test%20Job')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_already_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_job(u'TestJob', self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] already exists')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def already_exists_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_job(u'a Folder/TestJob', self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'job[a Folder/TestJob] already exists')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            jenkins.NotFoundException(),
            None,
            jenkins.NotFoundException(),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_job(u'TestJob', self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/createItem?name=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            jenkins.NotFoundException(),
            None,
            jenkins.NotFoundException(),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_job(u'a Folder/TestJob', self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/TestJob/api/json?tree=name')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/createItem?name=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[a Folder/TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetJobInfoTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        job_info = self.j.get_job_info(u'Test Job')

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/Test%20Job/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        job_info = self.j.get_job_info(u'a Folder/Test Job')

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/a%20Folder/job/Test%20Job/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_regex(self, jenkins_mock):
        jobs = [
            {u'name': u'my-job-1'},
            {u'name': u'my-job-2'},
            {u'name': u'your-job-1'},
            {u'name': u'Your-Job-1'},
            {u'name': u'my-project-1'},
        ]
        job_info_to_return = {u'jobs': jobs}
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        self.assertEqual(len(self.j.get_job_info_regex('her-job')), 0)
        self.assertEqual(len(self.j.get_job_info_regex('my-job-1')), 1)
        self.assertEqual(len(self.j.get_job_info_regex('my-job')), 2)
        self.assertEqual(len(self.j.get_job_info_regex('job')), 3)
        self.assertEqual(len(self.j.get_job_info_regex('project')), 1)
        self.assertEqual(len(self.j.get_job_info_regex('[Yy]our-[Jj]ob-1')), 2)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_job_info(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_job_info(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for job[TestJob]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/api/json?depth=0',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_job_info(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder_raise_HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/a%20Folder/job/TestJob/api/json?depth=0',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_job_info(u'a Folder/TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/a%20Folder/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'job[a Folder/TestJob] does not exist')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDebugJobInfoTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_debug_job_info(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        self.j.debug_job_info(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/Test%20Job/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)

        self.j.debug_job_info(u'a Folder/Test Job')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/a%20Folder/job/Test%20Job/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsReconfigJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job'}),
            None,
        ]

        self.j.reconfig_job(u'Test Job', self.config_xml)

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/Test%20Job/config.xml')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job'}),
            None,
        ]

        self.j.reconfig_job(u'a Folder/Test Job', self.config_xml)

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/a%20Folder/job/Test%20Job/config.xml')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsBuildJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]

        build_info = self.j.build_job(u'Test Job')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/Test%20Job/build')
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]

        build_info = self.j.build_job(u'a Folder/Test Job')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/a%20Folder/job/Test%20Job/build')
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_with_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]

        build_info = self.j.build_job(u'TestJob', token='some_token')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/build?token=some_token')
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder_with_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]

        build_info = self.j.build_job(u'a Folder/TestJob', token='some_token')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/a%20Folder/job/TestJob/build?token=some_token')
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_with_parameters_and_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]

        build_info = self.j.build_job(
            u'TestJob',
            parameters={'when': 'now', 'why': 'because I felt like it'},
            token='some_token')

        self.assertTrue('token=some_token' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertTrue('when=now' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertTrue('why=because+I+felt+like+it' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetJobsTestBase(JenkinsJobsTestBase):

    jobs_in_folder = [
        [
            {'name': 'my_job1'},
            {'name': 'my_folder1', 'jobs': None},
            {'name': 'my_job2'}
        ],
        # my_folder1 jobs
        [
            {'name': 'my_job3'},
            {'name': 'my_job4'}
        ]
    ]

    jobs_in_multiple_folders = copy.deepcopy(jobs_in_folder)
    jobs_in_multiple_folders[1].insert(
        0, {'name': 'my_folder2', 'jobs': None})
    jobs_in_multiple_folders.append(
        # my_folder1/my_folder2 jobs
        [
            {'name': 'my_job1'},
            {'name': 'my_job2'}
        ]
    )


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

        job_info = self.j.get_jobs()

        jobs[u'fullname'] = jobs[u'name']  # recursive search adds this
        self.assertEqual(job_info[0], jobs)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/api/json?tree=jobs[url,color,name,jobs]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_folders_simple(self, jenkins_mock):
        response = build_jobs_list_responses(
            self.jobs_in_folder, 'http://example.com/')
        jenkins_mock.side_effect = iter(response)

        jobs_info = self.j.get_jobs()

        expected_fullnames = [
            u"my_job1", u"my_job2"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_folders_additional_level(self, jenkins_mock):
        response = build_jobs_list_responses(
            self.jobs_in_folder, 'http://example.com/')
        jenkins_mock.side_effect = iter(response)

        jobs_info = self.j.get_jobs(folder_depth=1)

        expected_fullnames = [
            u"my_job1", u"my_job2",
            u"my_folder1/my_job3", u"my_folder1/my_job4"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)


class JenkinsGetAllJobsTest(JenkinsGetJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        response = build_jobs_list_responses(
            self.jobs_in_folder, 'http://example.com/')
        jenkins_mock.side_effect = iter(response)

        jobs_info = self.j.get_all_jobs()

        expected_fullnames = [
            u"my_job1", u"my_job2",
            u"my_folder1/my_job3", u"my_folder1/my_job4"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_multi_level(self, jenkins_mock):
        response = build_jobs_list_responses(
            self.jobs_in_multiple_folders, 'http://example.com/')
        jenkins_mock.side_effect = iter(response)

        jobs_info = self.j.get_all_jobs()

        expected_fullnames = [
            u"my_job1", u"my_job2",
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

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_folders_depth(self, jenkins_mock):
        response = build_jobs_list_responses(
            self.jobs_in_multiple_folders, 'http://example.com/')
        jenkins_mock.side_effect = iter(response)

        jobs_info = self.j.get_all_jobs(folder_depth=1)

        expected_fullnames = [
            u"my_job1", u"my_job2",
            u"my_folder1/my_job3", u"my_folder1/my_job4"
        ]
        self.assertEqual(len(expected_fullnames), len(jobs_info))
        got_fullnames = [job[u"fullname"] for job in jobs_info]
        self.assertEqual(expected_fullnames, got_fullnames)


class JenkinsJobsCountTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jobs = [
            {u'url': u'http://localhost:8080/job/guava/', u'color': u'notbuilt', u'name': u'guava'},
            {u'url': u'http://localhost:8080/job/kiwi/', u'color': u'blue', u'name': u'kiwi'},
            {u'url': u'http://localhost:8080/job/lemon/', u'color': u'red', u'name': u'lemon'}
        ]
        job_info_to_return = {u'jobs': jobs}
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        self.assertEqual(self.j.jobs_count(), 3)
        self._check_requests(jenkins_mock.call_args_list)


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
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/createItem'
            '?name=Test%20Job_2&mode=copy&from=Test%20Job')
        self.assertTrue(self.j.job_exists('Test Job_2'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
        ]

        self.j.copy_job(u'a Folder/Test Job', u'a Folder/Test Job_2')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/createItem'
            '?name=Test%20Job_2&mode=copy&from=Test%20Job')
        self.assertTrue(self.j.job_exists('a Folder/Test Job_2'))
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
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/createItem'
            '?name=TestJob_2&mode=copy&from=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.copy_job(u'a Folder/TestJob', u'a Folder/TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/createItem'
            '?name=TestJob_2&mode=copy&from=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[a Folder/TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_another_folder_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            jenkins.JenkinsException()
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.copy_job(u'a Folder/TestJob', u'another Folder/TestJob_2')
        self.assertEqual(
            str(context_manager.exception),
            ('copy[a Folder/TestJob to another Folder/TestJob_2] failed, '
             'source and destination folder must be the same'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsRenameJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
        ]

        self.j.rename_job(u'Test Job', u'Test Job_2')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/Test%20Job/doRename?newName=Test%20Job_2')
        self.assertTrue(self.j.job_exists('Test Job_2'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
        ]

        self.j.rename_job(u'a Folder/Test Job', u'a Folder/Test Job_2')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/Test%20Job/doRename?newName=Test%20Job_2')
        self.assertTrue(self.j.job_exists('Test Job_2'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.rename_job(u'TestJob', u'TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/doRename?newName=TestJob_2')
        self.assertEqual(
            str(context_manager.exception),
            'rename[TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.rename_job(u'a Folder/TestJob', u'a Folder/TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/TestJob/doRename?newName=TestJob_2')
        self.assertEqual(
            str(context_manager.exception),
            'rename[a Folder/TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_another_folder_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            jenkins.JenkinsException()
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.rename_job(u'a Folder/TestJob', u'another Folder/TestJob_2')
        self.assertEqual(
            str(context_manager.exception),
            ('rename[a Folder/TestJob to another Folder/TestJob_2] failed, '
             'source and destination folder must be the same'))
        self._check_requests(jenkins_mock.call_args_list)


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
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]

        self.j.delete_job(u'a Folder/Test Job')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/Test%20Job/doDelete')
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

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.delete_job(u'a Folder/TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/TestJob/doDelete')
        self.assertEqual(
            str(context_manager.exception),
            'delete[a Folder/TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsEnableJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]

        self.j.enable_job(u'TestJob')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/enable')
        self.assertTrue(self.j.job_exists('TestJob'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]

        self.j.enable_job(u'a Folder/TestJob')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/TestJob/enable')
        self.assertTrue(self.j.job_exists('a Folder/TestJob'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDisableJobTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job'}),
            json.dumps({'name': 'Test Job'}),
        ]

        self.j.disable_job(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/Test%20Job/disable')
        self.assertTrue(self.j.job_exists('Test Job'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job'}),
            json.dumps({'name': 'Test Job'}),
        ]

        self.j.disable_job(u'a Folder/Test Job')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/Test%20Job/disable')
        self.assertTrue(self.j.job_exists('a Folder/Test Job'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetJobNameTest(JenkinsJobsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        job_name_to_return = {u'name': 'Test Job'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)

        job_name = self.j.get_job_name(u'Test Job')

        self.assertEqual(job_name, 'Test Job')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/Test%20Job/api/json?tree=name')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        job_name_to_return = {u'name': 'Test Job'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)

        job_name = self.j.get_job_name(u'a Folder/Test Job')

        self.assertEqual(job_name, 'Test Job')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/a%20Folder/job/Test%20Job/api/json?tree=name')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()

        job_name = self.j.get_job_name(u'TestJob')

        self.assertEqual(job_name, None)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?tree=name')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder_return_none(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()

        job_name = self.j.get_job_name(u'a Folder/TestJob')

        self.assertEqual(job_name, None)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/a%20Folder/job/TestJob/api/json?tree=name')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_unexpected_job_name(self, jenkins_mock):
        job_name_to_return = {u'name': 'not the right name'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_job_name(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'Jenkins returned an unexpected job name {0} '
            '(expected: {1})'.format(job_name_to_return['name'], 'TestJob'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder_unexpected_job_name(self, jenkins_mock):
        job_name_to_return = {u'name': 'not the right name'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_job_name(u'a Folder/TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/a%20Folder/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'Jenkins returned an unexpected job name {0} (expected: '
            '{1})'.format(job_name_to_return['name'], 'a Folder/TestJob'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetJobFolderTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        folder, name = self.j._get_job_folder('my job')
        self.assertEqual(folder, '')
        self.assertEqual(name, 'my job')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_single_level(self, jenkins_mock):
        folder, name = self.j._get_job_folder('my folder/my job')
        self.assertEqual(folder, 'job/my folder/')
        self.assertEqual(name, 'my job')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_multi_level(self, jenkins_mock):
        folder, name = self.j._get_job_folder('folder1/folder2/my job')
        self.assertEqual(folder, 'job/folder1/job/folder2/')
        self.assertEqual(name, 'my job')
