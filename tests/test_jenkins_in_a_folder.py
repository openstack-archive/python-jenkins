import json
import socket
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from mock import patch, Mock
import six
from six.moves.urllib.error import HTTPError
from six.moves.urllib.request import build_opener

from tests.helper import jenkins


def get_mock_urlopen_return_value(a_dict=None):
    if a_dict is None:
        a_dict = {}
    return six.BytesIO(json.dumps(a_dict).encode('utf-8'))


class JenkinsTest(unittest.TestCase):


    def setUp(self):
        super(JenkinsTest, self).setUp()
        self.opener = build_opener()

    def _check_requests(self, requests):

        for req in requests:
            self._check_request(req[0][0])

    def _check_request(self, request):

        # taken from opener.open() in request
        # attribute request.type is only set automatically for python 3
        # requests, must use request.get_type() for python 2.7
        protocol = request.type or request.get_type()

        # check that building the request doesn't throw any exception
        meth_name = protocol + "_request"
        for processor in self.opener.process_request.get(protocol, []):
            meth = getattr(processor, meth_name)
            request = meth(request)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_config_in_a_folder_encodes_job_name(self, jenkins_mock):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.get_job_config(u'Test Job', 'A')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/A/job/Test%20Job/config.xml')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_assert_job_exists_in_a_folder__job_missing(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.assert_job_exists('NonExistent', folder='A')
        self.assertEqual(
            str(context_manager.exception),
            'job[NonExistent] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_assert_job_exists_in_a_folder__job_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.assert_job_exists('ExistingJob', folder='A')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_job_in_a_folder(self, jenkins_mock):
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

        j.create_job(u'Test Job', config_xml, 'A')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/A/createItem?name=Test%20Job')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_reconfig_job_in_a_folder(self, jenkins_mock):
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

        j.reconfig_job(u'Test Job', config_xml, 'A')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/A/job/Test%20Job/config.xml')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job_in_a_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(u'Test Job', folder='A')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/A/job/Test%20Job/build')
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job_in_a_folder__with_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(u'TestJob', token='some_token', folder='A')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/A/job/TestJob/build?token=some_token')
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job_in_a_folder__with_parameters_and_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(
            u'TestJob',
            parameters={'when': 'now', 'why': 'because I felt like it'},
            token='some_token', folder='A')

        self.assertTrue('token=some_token' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertTrue('when=now' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertTrue('why=because+I+felt+like+it' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertEqual(build_info, {'foo': 'bar'})
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_stop_build_in_a_folder(self, jenkins_mock):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.stop_build(u'Test Job', number=52, folder='A')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/A/job/Test%20Job/52/stop')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_in_a_folder_console_output(self, jenkins_mock):
        jenkins_mock.return_value = "build console output..."
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.get_build_console_output(u'Test Job', number=52, folder='A')

        self.assertEqual(build_info, jenkins_mock.return_value)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/A/job/Test%20Job/52/consoleText')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info_in_a_folder(self, jenkins_mock):
        build_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(build_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.get_build_info(u'Test Job', number=52, folder='A')

        self.assertEqual(build_info, build_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/A/job/Test%20Job/52/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info_in_a_folder(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_job_info(u'Test Job', folder='A')

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/A/job/Test%20Job/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)

    # TODO
    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_copy_job_in_a_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.copy_job(u'Test Job', u'Test Job_2', 'A')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/A/createItem'
            '?name=Test%20Job_2&mode=copy&from=Test%20Job')
        self.assertTrue(j.job_exists('Test Job_2'))
        self._check_requests(jenkins_mock.call_args_list)

    # TODO
    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_copy_job_in_a_folder__create_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.copy_job(u'TestJob', u'TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/createItem'
            '?name=TestJob_2&mode=copy&from=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_rename_job_in_a_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
            json.dumps({'name': 'Test Job_2'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.rename_job(u'Test Job', u'Test Job_2', 'A')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/A/job/Test%20Job/doRename?newName=Test%20Job_2')
        self.assertTrue(j.job_exists('Test Job_2', 'A'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_rename_job_in_a_folder__rename_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.rename_job(u'TestJob', u'TestJob_2', 'A')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/A/job/TestJob/doRename?newName=TestJob_2')
        self.assertEqual(
            str(context_manager.exception),
            'rename[TestJob_2] failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_job_in_a_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.delete_job(u'Test Job', 'A')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/A/job/Test%20Job/doDelete')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_job_in_a_folder__delete_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.delete_job(u'TestJob', 'A')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/A/job/TestJob/doDelete')
        self.assertEqual(
            str(context_manager.exception),
            'delete[TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_enable_job_in_a_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_job(u'TestJob', 'A')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/A/job/TestJob/enable')
        self.assertTrue(j.job_exists('TestJob', 'A'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_disable_job_in_a_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Job'}),
            json.dumps({'name': 'Test Job'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_job(u'Test Job', 'A')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/A/job/Test%20Job/disable')
        self.assertTrue(j.job_exists('Test Job', 'A'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name_in_a_folder(self, jenkins_mock):
        job_name_to_return = {u'name': 'Test Job'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_name = j.get_job_name(u'Test Job', 'A')

        self.assertEqual(job_name, 'Test Job')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/A/job/Test%20Job/api/json?tree=name')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name_in_a_folder__None(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_name = j.get_job_name(u'TestJob', 'A')

        self.assertEqual(job_name, None)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/A/job/TestJob/api/json?tree=name')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name_in_a_folder__unexpected_job_name(self, jenkins_mock):
        job_name_to_return = {u'name': 'not the right name'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_name(u'TestJob', 'A')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/A/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'Jenkins returned an unexpected job name {0} '
            '(expected: {1})'.format(job_name_to_return['name'], 'TestJob'))
        self._check_requests(jenkins_mock.call_args_list)
