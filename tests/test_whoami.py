import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase
from tests.helper import build_response_mock


class JenkinsWhoamiTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        user_to_return = \
            {u'absoluteUrl': u'https://example.com/jenkins/user/jsmith',
             u'description': None,
             u'fullName': u'John Smith',
             u'id': u'jsmith',
             u'property': [{},
                           {},
                           {},
                           {u'address': u'jsmith@example.com'},
                           {},
                           {},
                           {u'insensitiveSearch': False},
                           {}]}

        jenkins_mock.return_value = json.dumps(user_to_return)

        user = self.j.get_whoami()

        self.assertEqual(user, user_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('me/api/json?depth=0'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_raise_HTTPError(self, session_send_mock):
        session_send_mock.side_effect = iter([
            build_response_mock(404, reason="Not Found"),  # crumb
            build_response_mock(401, reason="Basic Auth Failed"),  # request
        ])

        with self.assertRaises(jenkins.JenkinsException):
            self.j.get_whoami()
        self.assertEqual(
            session_send_mock.call_args_list[1][0][1].url,
            self.make_url('me/api/json?depth=0'))
