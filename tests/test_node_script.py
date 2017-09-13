from mock import patch
from six.moves.urllib.parse import quote

import jenkins
from tests.base import JenkinsTestBase


class JenkinsNodeScriptTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_run_node_script(self, jenkins_mock):
        self.j.run_node_script(u'test node', u'println(\"Hello World!\")')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            self.make_url('computer/test%20node/scriptText'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_run_node_script_urlproof(self, jenkins_mock):
        self.j.run_node_script(u'test node', u'if (a == b && c ==d) { println(\"Yes\")}')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            self.make_url('computer/test%20node/scriptText'))
        self.assertIn(quote('&&'), jenkins_mock.call_args[0][0].data.decode('utf8'))
        self._check_requests(jenkins_mock.call_args_list)
