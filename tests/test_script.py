from mock import patch

import jenkins
from tests.base import JenkinsTestBase


class JenkinsScriptTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_run_script(self, jenkins_mock):
        self.j.run_script(u'println(\"Hello World!\")')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/scriptText')
        self._check_requests(jenkins_mock.call_args_list)

    # installation of plugins is done with the run_script method
    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_install_plugin(self, jenkins_mock):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.install_plugin("jabber")

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/scriptText')
        self._check_requests(jenkins_mock.call_args_list)
