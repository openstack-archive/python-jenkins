import json
from mock import patch

import jenkins
import requests_mock
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


class JenkinsNodesTestBase(JenkinsTestBase):

    def setUp(self):
        super(JenkinsNodesTestBase, self).setUp()
        self.node_info = {
            'displayName': 'test node',
            'totalExecutors': 5,
        }
        self.online_node_info = dict(self.node_info)
        self.online_node_info['offline'] = False
        self.offline_node_info = dict(self.node_info)
        self.offline_node_info['offline'] = True


class JenkinsGetNodesTest(JenkinsNodesTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.return_value = json.dumps({
            "computer": [{
                "displayName": "master",
                "offline": False
            }],
            "busyExecutors": 2})
        self.assertEqual(self.j.get_nodes(),
                         [{'name': 'master', 'offline': False}])
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.side_effect = [
            'Invalid JSON',
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_nodes()
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('computer/api/json?depth=0'))
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for server[{0}]'.format(
                self.make_url('')))
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_BadStatusLine(self, session_send_mock):
        session_send_mock.side_effect = jenkins.BadStatusLine(
            'not a valid status line')
        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_nodes()
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}]'.format(
                self.make_url('')))

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),        # crumb
            build_response_mock(499, reason="Unhandled Error"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_nodes()
        self.assertEqual(
            session_send_mock.call_args_list[1][0][1].url,
            self.make_url('computer/api/json?depth=0'))
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}]'.format(
                self.make_url('')))


class JenkinsGetNodeInfoTest(JenkinsNodesTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps(self.node_info),
        ]

        self._check_requests(jenkins_mock.call_args_list)
        self.assertEqual(self.j.get_node_info('test node'), self.node_info)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('computer/test%20node/api/json?depth=0'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.side_effect = [
            'Invalid JSON',
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_node_info('test_node')

        self._check_requests(jenkins_mock.call_args_list)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('computer/test_node/api/json?depth=0'))
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for node[test_node]')

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),        # crumb
            build_response_mock(499, reason="Unhandled Error"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_node_info('test_node')
        self.assertEqual(
            session_send_mock.call_args_list[1][0][1].url,
            self.make_url('computer/test_node/api/json?depth=0'))
        self.assertEqual(
            str(context_manager.exception),
            'node[test_node] does not exist')


class JenkinsAssertNodeExistsTest(JenkinsNodesTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_node_missing(self, jenkins_mock):
        jenkins_mock.side_effect = [None]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.assert_node_exists('NonExistentNode')

        self._check_requests(jenkins_mock.call_args_list)
        self.assertEqual(
            str(context_manager.exception),
            'node[NonExistentNode] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_node_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingNode'})
        ]
        self.j.assert_node_exists('ExistingNode')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDeleteNodeTest(JenkinsNodesTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps(self.node_info),
            None,
            None,
            None,
        ]

        self.j.delete_node('test node')

        self._check_requests(jenkins_mock.call_args_list)
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('computer/test%20node/doDelete'))
        self.assertFalse(self.j.node_exists('test node'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps(self.node_info),
            None,
            json.dumps(self.node_info),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.delete_node('test_node')

        self._check_requests(jenkins_mock.call_args_list)
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('computer/test_node/doDelete'))
        self.assertEqual(
            str(context_manager.exception),
            'delete[test_node] failed')


class JenkinsCreateNodeTest(JenkinsNodesTestBase):

    @requests_mock.Mocker()
    def test_simple(self, req_mock):
        req_mock.get(self.make_url(jenkins.CRUMB_URL))
        req_mock.post(self.make_url(jenkins.CREATE_NODE), status_code=200,
                      text='success', headers={'content-length': '7'})
        req_mock.get(
            self.make_url('computer/test%20node/api/json?depth=0'),
            [{'status_code': 404, 'headers': {'content-length': '9'},
              'text': 'NOT FOUND'},
             {'status_code': 200, 'json': {'displayName': 'test%20node'},
              'headers': {'content-length': '20'}}
             ])

        self.j.create_node('test node', exclusive=True)

        actual = req_mock.request_history[2]
        self.assertEqual(actual.url, self.make_url('computer/doCreateItem'))
        self.assertIn('name=test+node', actual.body)
        self.assertTrue(self.j.node_exists('test node'))

    @requests_mock.Mocker()
    def test_urlencode(self, req_mock):
        # resp 0 (don't care about this succeeding)
        req_mock.get(self.make_url(jenkins.CRUMB_URL))
        # resp 2
        req_mock.post(self.make_url(jenkins.CREATE_NODE), status_code=200,
                      text='success', headers={'content-length': '7'})
        # resp 1 & 3
        req_mock.get(
            self.make_url('computer/10.0.0.1%2Btest-node/api/json?depth=0'),
            [{'status_code': 404, 'headers': {'content-length': '9'},
              'text': 'NOT FOUND'},
             {'status_code': 200,
              'json': {'displayName': '10.0.0.1+test-node'},
              'headers': {'content-length': '20'}}
             ])

        params = {
            'port': '22',
            'username': 'juser',
            'credentialsId': '10f3a3c8-be35-327e-b60b-a3e5edb0e45f',
            'host': 'my.jenkins.slave1'
        }
        self.j.create_node(
            # Note the use of a URL-encodable character "+" here.
            '10.0.0.1+test-node',
            nodeDescription='my test slave',
            remoteFS='/home/juser',
            labels='precise',
            exclusive=True,
            launcher=jenkins.LAUNCHER_SSH,
            launcher_params=params)

        actual = req_mock.request_history[2].body
        # As python dicts do not guarantee order so the parameters get
        # re-ordered when it gets processed by requests, verify sections
        # of the URL with self.assertIn() instead of the entire URL
        self.assertIn(u'name=10.0.0.1%2Btest-node', actual)
        self.assertIn(u'type=hudson.slaves.DumbSlave%24DescriptorImpl', actual)
        self.assertIn(u'username%22%3A+%22juser', actual)
        self.assertIn(
            u'stapler-class%22%3A+%22hudson.plugins.sshslaves.SSHLauncher',
            actual)
        self.assertIn(u'host%22%3A+%22my.jenkins.slave1', actual)
        self.assertIn(
            u'credentialsId%22%3A+%2210f3a3c8-be35-327e-b60b-a3e5edb0e45f',
            actual)
        self.assertIn(u'port%22%3A+%2222', actual)
        self.assertIn(u'remoteFS%22%3A+%22%2Fhome%2Fjuser', actual)
        self.assertIn(u'labelString%22%3A+%22precise', actual)

    @requests_mock.Mocker()
    def test_already_exists(self, req_mock):
        req_mock.get(self.make_url(jenkins.CRUMB_URL))
        req_mock.get(
            self.make_url('computer/test_node/api/json?depth=0'),
            status_code=200, json=self.node_info,
            headers={'content-length': '20'}
        )

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_node('test_node')
        self.assertEqual(
            str(context_manager.exception),
            'node[test_node] already exists')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            None,
            None,
            None,
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_node('test_node')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('computer/doCreateItem'))
        self.assertEqual(
            str(context_manager.exception),
            'create[test_node] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsEnableNodeTest(JenkinsNodesTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps(self.offline_node_info),
            None,
        ]

        self.j.enable_node('test node')

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('computer/test%20node/'
                          'toggleOffline?offlineMessage='))

        jenkins_mock.side_effect = [json.dumps(self.online_node_info)]
        node_info = self.j.get_node_info('test node')
        self.assertEqual(node_info, self.online_node_info)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_offline_false(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps(self.online_node_info),
            None,
        ]

        self.j.enable_node('test_node')

        # Node was not offline; so enable_node skips toggle
        # Last call to jenkins was to check status
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('computer/test_node/api/json?depth=0'))

        jenkins_mock.side_effect = [json.dumps(self.online_node_info)]
        node_info = self.j.get_node_info('test_node')
        self.assertEqual(node_info, self.online_node_info)
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDisableNodeTest(JenkinsNodesTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps(self.online_node_info),
            None,
        ]

        self.j.disable_node('test node')

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('computer/test%20node/'
                          'toggleOffline?offlineMessage='))

        jenkins_mock.side_effect = [json.dumps(self.offline_node_info)]
        node_info = self.j.get_node_info('test node')
        self.assertEqual(node_info, self.offline_node_info)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_offline_true(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps(self.offline_node_info),
            None,
        ]

        self.j.disable_node('test_node')

        # Node was already offline; so disable_node skips toggle
        # Last call to jenkins was to check status
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('computer/test_node/api/json?depth=0'))

        jenkins_mock.side_effect = [json.dumps(self.offline_node_info)]
        node_info = self.j.get_node_info('test_node')
        self.assertEqual(node_info, self.offline_node_info)
        self._check_requests(jenkins_mock.call_args_list)
