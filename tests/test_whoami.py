import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase


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
            jenkins_mock.call_args[0][0].get_full_url(),
            self.make_url('me/api/json'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            self.make_url('me/api/json'),
            code=401,
            msg='basic auth failed',
            hdrs=[],
            fp=None)

        with self.assertRaises(jenkins.JenkinsException):
            self.j.get_whoami()
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            self.make_url('me/api/json'))
        self._check_requests(jenkins_mock.call_args_list)
