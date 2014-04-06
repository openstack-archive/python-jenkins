import json
import unittest

from mock import patch

from tests.helper import jenkins, StringIO


class JenkinsTest(unittest.TestCase):

    def test_constructor(self):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic dGVzdDp0ZXM=\n')
        self.assertEqual(j.crumb, None)

        j = jenkins.Jenkins('http://example.com', 'test', 'test')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic dGVzdDp0ZXM=\n')
        self.assertEqual(j.crumb, None)

        j = jenkins.Jenkins('http://example.com')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, None)
        self.assertEqual(j.crumb, None)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_config_encodes_job_name(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.get_job_config(u'Test Job')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/Test%20Job/config.xml')

    @patch('jenkins.urlopen')
    def test_maybe_add_crumb(self, jenkins_mock):
        jenkins_mock.return_value = StringIO()
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        j.maybe_add_crumb(request)

    @patch('jenkins.urlopen')
    def test_maybe_add_crumb__with_data(self, jenkins_mock):
        crumb_data = {
            "crumb": "dab177f483b3dd93483ef6716d8e792d",
            "crumbRequestField": ".crumb",
        }
        jenkins_mock.return_value = StringIO(json.dumps(crumb_data))
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        j.maybe_add_crumb(request)

        self.assertEqual(j.crumb, crumb_data)

    @patch('jenkins.urlopen')
    def test_jenkins_open(self, jenkins_mock):
        crumb_data = {
            "crumb": "dab177f483b3dd93483ef6716d8e792d",
            "crumbRequestField": ".crumb",
        }
        data = {'foo': 'bar'}
        jenkins_mock.side_effect = [
            StringIO(json.dumps(crumb_data)),
            StringIO(json.dumps(data)),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        response = j.jenkins_open(request)
        self.assertEqual(response, json.dumps(data))

    @patch('jenkins.urlopen')
    def test_jenkins_open__403(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        try:
            j.jenkins_open(request, add_crumb=False)
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'Error in request.Possibly authentication failed [401]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_job(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        config_xml = """<matrix-project><actions/><description>Foo</description></matrix-project>"""
        jenkins_mock.side_effect = [
            None,
            None,
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.create_job(u'TestJob', config_xml)

        self.assertEqual(jenkins_mock.call_args_list[1][0][0].get_full_url(),
                         'http://example.com/createItem?name=TestJob')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_job__already_exists(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        config_xml = """<matrix-project><actions/><description>Foo</description></matrix-project>"""
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.create_job(u'TestJob', config_xml)
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'job[TestJob] already exists')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_job__create_failed(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        config_xml = """<matrix-project><actions/><description>Foo</description></matrix-project>"""
        jenkins_mock.side_effect = [
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.create_job(u'TestJob', config_xml)
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'create[TestJob] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_reconfig_job(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        config_xml = """<matrix-project><actions/><description>Foo</description></matrix-project>"""
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.reconfig_job(u'TestJob', config_xml)

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/config.xml')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(u'TestJob')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/build')
        self.assertEqual(build_info, {'foo': 'bar'})

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job__with_token(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(u'TestJob', token='some_token')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/build?token=some_token')
        self.assertEqual(build_info, {'foo': 'bar'})

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job__with_parameters_and_token(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(
            u'TestJob',
            parameters={'when': 'now', 'why': 'because I felt like it'},
            token='some_token')

        self.assertTrue('token=some_token' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertTrue('when=now' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertTrue('why=because+I+felt+like+it' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertEqual(build_info, {'foo': 'bar'})

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job__job_doesnt_exist(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.build_job(u'TestJob')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'no such job[TestJob]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_stop_build(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.stop_build(u'TestJob', number=52)

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/52/stop')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_console_output(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.return_value = "build console output..."
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.get_build_console_output(u'TestJob', number=52)

        self.assertEqual(build_info, jenkins_mock.return_value)
        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/52/consoleText')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_console_output__None(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_build_console_output(u'TestJob', number=52)
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_console_output__invalid_json(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.return_value = 'Invalid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_build_console_output(u'TestJob', number=52)
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_console_output__HTTPError(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/52/consoleText',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_build_console_output(u'TestJob', number=52)
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        build_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(build_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.get_build_info(u'TestJob', number=52)

        self.assertEqual(build_info, build_info_to_return)
        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/52/api/json?depth=0')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info__None(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_build_info(u'TestJob', number=52)
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info__invalid_json(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.return_value = 'Invalid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_build_info(u'TestJob', number=52)
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'Could not parse JSON info for job[TestJob] number[52]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info__HTTPError(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/api/json?depth=0',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_build_info(u'TestJob', number=52)
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_job_info(u'TestJob')

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/api/json?depth=0')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info__None(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        # Note that if we commit to pytest, we can use pytest.raises here...
        try:
            j.get_job_info(u'TestJob')
            self.fail("This should've failed with JenkinsException")
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'job[TestJob] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info__invalid_json(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.return_value = 'Invalid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        # Note that if we commit to pytest, we can use pytest.raises here...
        try:
            j.get_job_info(u'TestJob')
            self.fail("This should've failed with JenkinsException")
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'Could not parse JSON info for job[TestJob]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info__HTTPError(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/api/json?depth=0',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        # Note that if we commit to pytest, we can use pytest.raises here...
        try:
            j.get_job_info(u'TestJob')
            self.fail("This should've failed with JenkinsException")
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'job[TestJob] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_debug_job_info(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.debug_job_info(u'TestJob')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/api/json?depth=0')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_jobs(self, jenkins_mock):
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
        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/api/json')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info(self, jenkins_mock):
        job_info_to_return = {
            u'jobs': {
                u'url': u'http://your_url_here/job/my_job/',
                u'color': u'blue',
                u'name': u'my_job',
            }
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_info()

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/api/json')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/api/json?depth=0',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_info()
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'Error communicating with server[http://example.com/]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__BadStatusLine(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.BadStatusLine('not a valid status line')
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_info()
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), 'Error communicating with server[http://example.com/]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__ValueError(self, jenkins_mock):
        jenkins_mock.return_value = 'not valid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_info()
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'Could not parse JSON info for server[http://example.com/]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_copy_job(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob_2'}),
            json.dumps({'name': 'TestJob_2'}),
            json.dumps({'name': 'TestJob_2'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.copy_job(u'TestJob', u'TestJob_2')

        self.assertTrue(j.job_exists('TestJob_2'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_copy_job__create_failed(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.copy_job(u'TestJob', u'TestJob_2')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'create[TestJob_2] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_rename_job(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob_2'}),
            json.dumps({'name': 'TestJob_2'}),
            json.dumps({'name': 'TestJob_2'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.rename_job(u'TestJob', u'TestJob_2')

        self.assertTrue(j.job_exists('TestJob_2'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_rename_job__rename_failed(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.rename_job(u'TestJob', u'TestJob_2')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'rename[TestJob_2] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_job(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.delete_job(u'TestJob')

        self.assertFalse(j.job_exists('TestJob'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_job__delete_failed(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.delete_job(u'TestJob')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'delete[TestJob] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_enable_job(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_job(u'TestJob')

        self.assertTrue(j.job_exists('TestJob'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_disable_job(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_job(u'TestJob')

        self.assertTrue(j.job_exists('TestJob'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        job_name_to_return = {u'name': 'TestJob'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_name = j.get_job_name(u'TestJob')

        self.assertEqual(job_name, 'TestJob')
        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/api/json?tree=name')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name__None(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_name = j.get_job_name(u'TestJob')

        self.assertEqual(job_name, None)
        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/api/json?tree=name')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name__unexpected_job_name(self, jenkins_mock):
        """
        The job name parameter specified should be urlencoded properly.
        """
        job_name_to_return = {u'name': 'not the right name'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_job_name(u'TestJob')
            self.fail("This should've failed with JenkinsException")
        except jenkins.JenkinsException as exc:
            self.assertEqual(str(exc), "Jenkins returned an unexpected job name")

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_cancel_queue(self, jenkins_mock):
        job_name_to_return = {u'name': 'TestJob'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.cancel_queue(52)

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/queue/item/52/cancelQueue')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_node_info(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        self.assertEqual(j.get_node_info('test_node'), node_info)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_node_info__invalid_json(self, jenkins_mock):
        jenkins_mock.side_effect = [
            'Invalid JSON',
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_node_info('test_node')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'Could not parse JSON info for node[test_node]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_node_info__HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.get_node_info('test_node')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'node[test_node] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_node(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.delete_node('test_node')

        self.assertFalse(j.node_exists('test_node'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_node__delete_failed(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.delete_node('test_node')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'delete[test_node] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_node(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            None,
            None,
            json.dumps(node_info),
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.create_node('test_node', exclusive=True)

        self.assertTrue(j.node_exists('test_node'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_node__node_already_exists(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.create_node('test_node')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'node[test_node] already exists')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_node__create_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        try:
            j.create_node('test_node')
        except jenkins.JenkinsException as exc:
            self.assertEqual(
                str(exc),
                'create[test_node] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_enable_node(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_node('test_node')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_enable_node__offline_False(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_node('test_node')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_disable_node(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_node('test_node')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_disable_node__offline_True(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_node('test_node')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_queue_info(self, jenkins_mock):
        queue_info_to_return = {
            'items': {
                u'task': {
                    u'url': u'http://your_url/job/my_job/',
                    u'color': u'aborted_anime',
                    u'name': u'my_job'
                },
                u'stuck': False,
                u'actions': [
                    {
                        u'causes': [
                            {
                                u'shortDescription': u'Started by timer',
                            },
                        ],
                    },
                ],
                u'buildable': False,
                u'params': u'',
                u'buildableStartMilliseconds': 1315087293316,
                u'why': u'Build #2,532 is already in progress (ETA:10 min)',
                u'blocked': True,
            }
        }
        jenkins_mock.return_value = json.dumps(queue_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        queue_info = j.get_queue_info()

        self.assertEqual(queue_info, queue_info_to_return['items'])
        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/queue/api/json?depth=0')
