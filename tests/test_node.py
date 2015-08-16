import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase


class JenkinsGetNodesTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.return_value = json.dumps({
            "computer": [{
                "displayName": "master",
                "offline": False
            }],
            "busyExecutors": 2})
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        self.assertEqual(j.get_nodes(),
                         [{'name': 'master', 'offline': False}])
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.side_effect = [
            'Invalid JSON',
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_nodes()
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_raise_BadStatusLine(self, urlopen_mock):
        urlopen_mock.side_effect = jenkins.BadStatusLine('not a valid status line')
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            j.get_nodes()
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')
        self._check_requests(urlopen_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_nodes()
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetNodeInfoTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        self.assertEqual(j.get_node_info('test node'), node_info)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test%20node/api/json?depth=0')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.side_effect = [
            'Invalid JSON',
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_node_info('test_node')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for node[test_node]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_node_info('test_node')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'node[test_node] does not exist')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsAssertNodeExistsTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_node_missing(self, jenkins_mock):
        jenkins_mock.side_effect = [None]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.assert_node_exists('NonExistentNode')
        self.assertEqual(
            str(context_manager.exception),
            'node[NonExistentNode] does not exist')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test__node_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingNode'})
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.assert_node_exists('ExistingNode')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDeleteNodeTest(JenkinsTestBase):

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

        j.delete_node('test node')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/computer/test%20node/doDelete')
        self.assertFalse(j.node_exists('test node'))
        self._check_requests(jenkins_mock.call_args_list)

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

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.delete_node('test_node')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/computer/test_node/doDelete')
        self.assertEqual(
            str(context_manager.exception),
            'delete[test_node] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsCreateNodeTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_node(self, jenkins_mock):
        node_info = {
            'displayName': 'test node',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            None,
            None,
            json.dumps(node_info),
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.create_node('test node', exclusive=True)

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url().split('?')[0],
            'http://example.com/computer/doCreateItem')
        self.assertTrue(j.node_exists('test node'))
        self._check_requests(jenkins_mock.call_args_list)

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

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.create_node('test_node')
        self.assertEqual(
            str(context_manager.exception),
            'node[test_node] already exists')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_node__create_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.create_node('test_node')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url().split('?')[0],
            'http://example.com/computer/doCreateItem')
        self.assertEqual(
            str(context_manager.exception),
            'create[test_node] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsEnableNodeTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        expected_node_info = {
            'displayName': 'test node',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [
            json.dumps(expected_node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_node('test node')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test%20node/' +
            'toggleOffline?offlineMessage=')

        expected_node_info = {
            'displayName': 'test node',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [json.dumps(expected_node_info)]
        node_info = j.get_node_info('test node')
        self.assertEqual(node_info, expected_node_info)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_offline_false(self, jenkins_mock):
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

        # Node was not offline; so enable_node skips toggle
        # Last call to jenkins was to check status
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')

        expected_node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [json.dumps(expected_node_info)]
        node_info = j.get_node_info('test_node')
        self.assertEqual(node_info, expected_node_info)
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDisableNodeTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        node_info = {
            'displayName': 'test node',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_node('test node')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test%20node/' +
            'toggleOffline?offlineMessage=')

        expected_node_info = {
            'displayName': 'test node',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [json.dumps(expected_node_info)]
        node_info = j.get_node_info('test node')
        self.assertEqual(node_info, expected_node_info)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_offline_true(self, jenkins_mock):
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

        # Node was already offline; so disable_node skips toggle
        # Last call to jenkins was to check status
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')

        expected_node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [json.dumps(expected_node_info)]
        node_info = j.get_node_info('test_node')
        self.assertEqual(node_info, expected_node_info)
        self._check_requests(jenkins_mock.call_args_list)
