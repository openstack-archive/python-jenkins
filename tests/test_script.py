from mock import patch

import jenkins
from tests.base import JenkinsTestBase


class JenkinsScriptTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_run_script(self, jenkins_mock):
        self.j.run_script(u'println(\"Hello World!\")')

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            u'http://example.com/scriptText')
        self._check_requests(jenkins_mock.call_args_list)
