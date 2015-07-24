import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


class JenkinsGetJobConfigTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_encodes_job_name(self, jenkins_mock):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.get_job_config(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/Test%20Job/config.xml')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsAssertJobExistsTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_job_missing(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.assert_job_exists('NonExistent')
        self.assertEqual(
            str(context_manager.exception),
            'job[NonExistent] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_job_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.assert_job_exists('ExistingJob')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsCreateJobTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        config_xml = """
            <matrix-project>
                <actions/>
                <description>Foo</description>
            </matrix-project>"""
        jenkins_mock.side_effect = [
            jenkins.NotFoundException(),
            None,
            json.dumps({'name': 'Test Job'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.create_job(u'Test Job', config_xml)

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            'http://example.com/createItem?name=Test%20Job')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_already_exists(self, jenkins_mock):
        config_xml = """
            <matrix-project>
                <actions/>
                <description>Foo</description>
            </matrix-project>"""
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.create_job(u'TestJob', config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] already exists')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        config_xml = """
            <matrix-project>
                <actions/>
                <description>Foo</description>
            </matrix-project>"""
        jenkins_mock.side_effect = [
            jenkins.NotFoundException(),
            None,
            jenkins.NotFoundException(),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.create_job(u'TestJob', config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            'http://example.com/createItem?name=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetJobInfoTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_job_info(u'Test Job')

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/Test%20Job/api/json?depth=0')
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
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        self.assertEqual(len(j.get_job_info_regex('her-job')), 0)
        self.assertEqual(len(j.get_job_info_regex('my-job-1')), 1)
        self.assertEqual(len(j.get_job_info_regex('my-job')), 2)
        self.assertEqual(len(j.get_job_info_regex('job')), 3)
        self.assertEqual(len(j.get_job_info_regex('project')), 1)
        self.assertEqual(len(j.get_job_info_regex('[Yy]our-[Jj]ob-1')), 2)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_info(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_info(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for job[TestJob]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_info(u'TestJob')
        self.assertEqual(
            session_send_mock.call_args_list[1][0][1].url,
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] does not exist')


class JenkinsDebugJobInfoTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_debug_job_info(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.debug_job_info(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/Test%20Job/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsReconfigJobTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        config_xml = """
            <matrix-project>
                <actions/>
                <description>Foo</description>
            </matrix-project>"""
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job'}),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.reconfig_job(u'Test Job', config_xml)

        self.assertEqual(jenkins_mock.call_args[0][0].url,
                         u'http://example.com/job/Test%20Job/config.xml')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsBuildJobTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(u'Test Job')

        self.assertEqual(jenkins_mock.call_args[0][0].url,
                         u'http://example.com/job/Test%20Job/build')
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_with_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(u'TestJob', token='some_token')

        self.assertEqual(jenkins_mock.call_args[0][0].url,
                         u'http://example.com/job/TestJob/build?token=some_token')
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_with_parameters_and_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(
            u'TestJob',
            parameters={'when': 'now', 'why': 'because I felt like it'},
            token='some_token')

        self.assertTrue('token=some_token' in jenkins_mock.call_args[0][0].url)
        self.assertTrue('when=now' in jenkins_mock.call_args[0][0].url)
        self.assertTrue('why=because+I+felt+like+it' in jenkins_mock.call_args[0][0].url)
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetJobsTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jobs = {
            u'url': u'http://your_url_here/job/my_job/',
            u'color': u'blue',
            u'name': u'my_job',
        }
        job_info_to_return = {u'jobs': jobs}
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_jobs()

        self.assertEqual(job_info, jobs)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/api/json')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsJobsCountTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jobs = [
            {u'url': u'http://localhost:8080/job/guava/', u'color': u'notbuilt', u'name': u'guava'},
            {u'url': u'http://localhost:8080/job/kiwi/', u'color': u'blue', u'name': u'kiwi'},
            {u'url': u'http://localhost:8080/job/lemon/', u'color': u'red', u'name': u'lemon'}
        ]
        job_info_to_return = {u'jobs': jobs}
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        self.assertEqual(j.jobs_count(), 3)
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsCopyJobTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_copy_job(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.copy_job(u'Test Job', u'Test Job_2')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/createItem'
            '?name=Test%20Job_2&mode=copy&from=Test%20Job')
        self.assertTrue(j.job_exists('Test Job_2'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_copy_job__create_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.copy_job(u'TestJob', u'TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/createItem'
            '?name=TestJob_2&mode=copy&from=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsRenameJobTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_rename_job(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.rename_job(u'Test Job', u'Test Job_2')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/Test%20Job/doRename?newName=Test%20Job_2')
        self.assertTrue(j.job_exists('Test Job_2'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_rename_job__rename_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.rename_job(u'TestJob', u'TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/TestJob/doRename?newName=TestJob_2')
        self.assertEqual(
            str(context_manager.exception),
            'rename[TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDeleteJobTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.delete_job(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/Test%20Job/doDelete')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.delete_job(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/TestJob/doDelete')
        self.assertEqual(
            str(context_manager.exception),
            'delete[TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsEnableJobTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_job(u'TestJob')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/TestJob/enable')
        self.assertTrue(j.job_exists('TestJob'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDisableJobTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job'}),
            json.dumps({'name': 'Test Job'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_job(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/Test%20Job/disable')
        self.assertTrue(j.job_exists('Test Job'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetJobNameTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        job_name_to_return = {u'name': 'Test Job'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_name = j.get_job_name(u'Test Job')

        self.assertEqual(job_name, 'Test Job')
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/Test%20Job/api/json?tree=name')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_name = j.get_job_name(u'TestJob')

        self.assertEqual(job_name, None)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/job/TestJob/api/json?tree=name')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_unexpected_job_name(self, jenkins_mock):
        job_name_to_return = {u'name': 'not the right name'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_name(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'Jenkins returned an unexpected job name {0} '
            '(expected: {1})'.format(job_name_to_return['name'], 'TestJob'))
        self._check_requests(jenkins_mock.call_args_list)
