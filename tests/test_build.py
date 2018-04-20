import json

import collections
from mock import patch

import jenkins
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


class JenkinsBuildConsoleTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.return_value = "build console output..."

        build_info = self.j.get_build_console_output(u'Test Job', number=52)

        self.assertEqual(build_info, jenkins_mock.return_value)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/52/consoleText'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.return_value = "build console output..."

        build_info = self.j.get_build_console_output(u'a Folder/Test Job', number=52)

        self.assertEqual(build_info, jenkins_mock.return_value)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/a%20Folder/job/Test%20Job/52/consoleText'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_console_output(u'A Folder/TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[A Folder/TestJob] number[52] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'

        console_output = self.j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(console_output, jenkins_mock.return_value)

    @patch('jenkins.requests.Session.send')
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(
            session_send_mock.call_args_list[1][0][0].url,
            self.make_url('job/TestJob/52/consoleText'))
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')

    @patch('jenkins.requests.Session.send')
    def test_in_folder_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_console_output(u'a Folder/TestJob', number=52)
        self.assertEqual(
            session_send_mock.call_args_list[1][0][0].url,
            self.make_url('job/a%20Folder/job/TestJob/52/consoleText'))
        self.assertEqual(
            str(context_manager.exception),
            'job[a Folder/TestJob] number[52] does not exist')


class JenkinsBuildInfoTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        build_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(build_info_to_return)

        build_info = self.j.get_build_info(u'Test Job', number=52)

        self.assertEqual(build_info, build_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/52/api/json?depth=0'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        build_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(build_info_to_return)

        build_info = self.j.get_build_info(u'a Folder/Test Job', number=52)

        self.assertEqual(build_info, build_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/a%20Folder/job/Test%20Job/52/api/json?depth=0'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for job[TestJob] number[52]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_in_folder_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_info(u'a Folder/TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[a Folder/TestJob] number[52] does not exist')


class JenkinsStopBuildTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        self.j.stop_build(u'Test Job', number=52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/52/stop'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):

        self.j.stop_build(u'a Folder/Test Job', number=52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/a%20Folder/job/Test%20Job/52/stop'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDeleteBuildTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        self.j.delete_build(u'Test Job', number=52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/52/doDelete'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):

        self.j.delete_build(u'a Folder/Test Job', number=52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/a%20Folder/job/Test%20Job/52/doDelete'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsListRunningBuildsTest(JenkinsTestBase):
    @patch.object(jenkins.Jenkins, 'get_node_info')
    @patch.object(jenkins.Jenkins, 'get_nodes')
    def test_with_builds_master(self, nodes_mock, node_info_mock):
        nodes_to_return = [{
            'name': "master", 'offline': False
        }]
        nodes_mock.return_value = nodes_to_return
        build = {
            "actions": [
                {
                    "parameters": [
                        {
                            "name": "FOO",
                            "value": "foo"
                        },
                        {
                            "name": "BAR",
                            "value": "bar"
                        }
                    ]
                },
                {
                    "causes": [
                        {
                            "shortDescription": "Started by user foo",
                            "userId": "foo",
                            "userName": "Foo Bar"
                        }
                    ]
                }
            ],
            "artifacts": [],
            "building": True,
            "description": None,
            "duration": 0,
            "estimatedDuration": 20148,
            "executor": {},
            "fullDisplayName": "test #1",
            "id": "2015-09-14_20-25-42",
            "keepLog": False,
            "number": 1,
            "result": None,
            "timestamp": 1442262342729,
            "url": self.make_url('job/test/1/'),
            "builtOn": "",
            "changeSet": {
                "items": [],
                "kind": None
            },
            "culprits": []
        }
        node_info_to_return = {
            "executors": [
                {
                    "currentExecutable": None,
                    "currentWorkUnit": None,
                    "idle": True,
                    "likelyStuck": False,
                    "number": 0,
                    "progress": -1
                },
                {
                    "currentExecutable": build,
                    "currentWorkUnit": {},
                    "idle": False,
                    "likelyStuck": False,
                    "number": 1,
                    "progress": 14
                }
            ],
        }
        node_info_mock.return_value = node_info_to_return
        builds = self.j.get_running_builds()
        self.assertEqual([{'name': 'test',
                           'number': 1,
                           'node': '(master)',
                           'executor': 1,
                           'url': self.make_url('job/test/1/')}], builds)

    @patch.object(jenkins.Jenkins, 'get_node_info')
    @patch.object(jenkins.Jenkins, 'get_nodes')
    def test_with_builds_non_master(self, nodes_mock, node_info_mock):
        nodes_to_return = [{
            'name': "foo-slave", 'offline': False
        }]
        nodes_mock.return_value = nodes_to_return
        build = {
            "actions": [
                {
                    "parameters": [
                        {
                            "name": "FOO",
                            "value": "foo"
                        },
                        {
                            "name": "BAR",
                            "value": "bar"
                        }
                    ]
                },
                {
                    "causes": [
                        {
                            "shortDescription": "Started by user foo",
                            "userId": "foo",
                            "userName": "Foo Bar"
                        }
                    ]
                }
            ],
            "artifacts": [],
            "building": True,
            "description": None,
            "duration": 0,
            "estimatedDuration": 20148,
            "executor": {},
            "fullDisplayName": "test #1",
            "id": "2015-09-14_20-25-42",
            "keepLog": False,
            "number": 15,
            "result": None,
            "timestamp": 1442262342729,
            "url": self.make_url("job/test/15/"),
            "builtOn": "",
            "changeSet": {
                "items": [],
                "kind": None
            },
            "culprits": []
        }
        node_info_to_return = {
            "executors": [
                {
                    "currentExecutable": None,
                    "currentWorkUnit": None,
                    "idle": True,
                    "likelyStuck": False,
                    "number": 1,
                    "progress": -1
                },
                {
                    "currentExecutable": build,
                    "currentWorkUnit": {},
                    "idle": False,
                    "likelyStuck": False,
                    "number": 0,
                    "progress": 14
                }
            ],
        }
        node_info_mock.return_value = node_info_to_return
        builds = self.j.get_running_builds()
        self.assertEqual([{'name': 'test',
                           'number': 15,
                           'node': 'foo-slave',
                           'executor': 0,
                           'url': self.make_url('job/test/15/')}], builds)

    @patch.object(jenkins.Jenkins, 'get_node_info')
    @patch.object(jenkins.Jenkins, 'get_nodes')
    def test_with_no_builds(self, nodes_mock, node_info_mock):
        nodes_to_return = [{
            'name': "master", 'offline': False
        }]
        nodes_mock.return_value = nodes_to_return
        node_info_to_return = {
            "executors": [
                {
                    "currentExecutable": None,
                    "currentWorkUnit": None,
                    "idle": True,
                    "likelyStuck": False,
                    "number": 0,
                    "progress": -1
                }
            ]
        }
        node_info_mock.return_value = node_info_to_return
        builds = self.j.get_running_builds()
        self.assertEqual([], builds)

    @patch.object(jenkins.Jenkins, 'get_node_info')
    @patch.object(jenkins.Jenkins, 'get_nodes')
    def test_broken_slave(self, nodes_mock, node_info_mock):
        nodes_to_return = [{
            'name': "foo-slave", 'offline': False
        }]
        nodes_mock.return_value = nodes_to_return

        def side_effect(*args, **kwargs):
            if 'depth' in kwargs and kwargs['depth'] > 0:
                raise jenkins.JenkinsException(
                    "Error in request. Possibly authentication failed"
                    "[500]: Server Error")
            else:
                return {"success": True}

        node_info_mock.side_effect = side_effect
        builds = self.j.get_running_builds()
        # Should treat the slave as not running any builds
        self.assertEqual([], builds)

    @patch.object(jenkins.Jenkins, 'get_node_info')
    @patch.object(jenkins.Jenkins, 'get_nodes')
    def test_placeholder_task_in_queue(self, nodes_mock, node_info_mock):
        nodes_to_return = [{
            'name': "foo-slave", 'offline': False
        }]
        nodes_mock.return_value = nodes_to_return
        node_info_to_return = {
            "executors": [
                {
                    "currentExecutable": None,
                    "currentWorkUnit": None,
                    "idle": True,
                    "likelyStuck": False,
                    "number": 1,
                    "progress": -1
                },
                {
                    'currentExecutable': {
                        '_class': (
                            'org.jenkinsci.plugins.workflow.support.steps.'
                            'ExecutorStepExecution$PlaceholderTask$'
                            'PlaceholderExecutable'
                        )
                    },
                    'currentWorkUnit': {},
                    'idle': False,
                    'likelyStuck': False,
                    'number': 1,
                    'progress': 0
                }
            ],
        }
        node_info_mock.return_value = node_info_to_return
        builds = self.j.get_running_builds()
        self.assertEqual([], builds)


class JenkinsBuildJobUrlTest(JenkinsTestBase):

    def test_params_as_dict(self):
        token = 'token123'
        params = [
            ('m_select', 'value1'),
            ('s_select', 's_select2')
        ]
        parameters = collections.OrderedDict(params)
        self.assertEqual(
            self.j.build_job_url('Test Job', parameters=parameters, token=token),
            self.make_url(
                'job/Test%20Job/buildWithParameters?m_select=value1'
                '&s_select=s_select2&token=token123'))

    def test_params_as_list(self):
        token = 'token123'
        params = [
            ('m_select', 'value1',),
            ('m_select', 'value3'),
            ('s_select', 's_select2')
        ]
        self.assertEqual(
            self.j.build_job_url('Test Job', parameters=params, token=token),
            self.make_url(
                'job/Test%20Job/buildWithParameters?m_select=value1'
                '&m_select=value3&s_select=s_select2&token=token123'))


class JenkinsBuildEnvVarUrlTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.return_value = '{}'
        ret = self.j.get_build_env_vars(u'Test Job', number=52, depth=1)
        self.assertEqual(ret, json.loads(jenkins_mock.return_value))
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/52/injectedEnvVars/api/json?depth=1'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.return_value = '{}'
        ret = self.j.get_build_env_vars(u'a Folder/Test Job', number=52, depth=1)
        self.assertEqual(ret, json.loads(jenkins_mock.return_value))
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/a%20Folder/job/Test%20Job/52/injectedEnvVars/api/json?depth=1'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_return_none(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])
        ret = self.j.get_build_env_vars(u'TestJob', number=52)
        self.assertIsNone(ret)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_open_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_env_vars(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_env_vars(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for job[TestJob] number[52]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(401, reason="Not Authorised"),  # crumb
            build_response_mock(401, reason="Not Authorised"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_env_vars(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request. Possibly authentication failed [401]: Not Authorised')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_in_folder_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(401, reason="Not Authorised"),  # crumb
            build_response_mock(401, reason="Not Authorised"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_env_vars(u'a Folder/TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request. Possibly authentication failed [401]: Not Authorised')


class JenkinsBuildTestReportUrlTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.return_value = '{}'
        ret = self.j.get_build_test_report(u'Test Job', number=52, depth=1)
        self.assertEqual(ret, json.loads(jenkins_mock.return_value))
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/52/testReport/api/json?depth=1'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_in_folder(self, jenkins_mock):
        jenkins_mock.return_value = '{}'
        ret = self.j.get_build_test_report(u'a Folder/Test Job', number=52, depth=1)
        self.assertEqual(ret, json.loads(jenkins_mock.return_value))
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/a%20Folder/job/Test%20Job/52/testReport/api/json?depth=1'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_return_none(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(404, reason="Not Found"),  # request
        ])
        ret = self.j.get_build_test_report(u'TestJob', number=52)
        self.assertIsNone(ret)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_open_return_none(self, jenkins_mock):
        jenkins_mock.return_value = None

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_test_report(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_test_report(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for job[TestJob] number[52]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(401, reason="Not Authorised"),  # crumb
            build_response_mock(401, reason="Not Authorised"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_test_report(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request. Possibly authentication failed [401]: Not Authorised')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_in_folder_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(401, reason="Not Authorised"),  # crumb
            build_response_mock(401, reason="Not Authorised"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_build_test_report(u'a Folder/TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request. Possibly authentication failed [401]: Not Authorised')
