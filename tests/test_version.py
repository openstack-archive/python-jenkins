from mock import patch, Mock
import six

import jenkins
from tests.base import JenkinsTestBase


class JenkinsVersionTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_some_version(self, jenkins_mock):
        mock_response = Mock()
        if six.PY2:
            config = {'info.return_value.getheader.return_value': 'Version42'}

        if six.PY3:
            config = {'getheader.return_value': 'Version42'}

        mock_response.configure_mock(**config)
        jenkins_mock.side_effect = [mock_response]
        self.assertEqual(self.j.get_version(), 'Version42')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            self.make_url(''),
            code=503,
            msg="internal server error",
            hdrs=[],
            fp=None)
        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_version()
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}/]'.format(self.base_url))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_BadStatusLine(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.BadStatusLine('not a valid status line')
        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_version()
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}/]'.format(self.base_url))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_empty_response(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.EmptyResponseException(
            "Error communicating with server[{0}/]: empty response".
            format(self.base_url))
        with self.assertRaises(jenkins.EmptyResponseException) as context_manager:
            self.j.get_version()
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[{0}/]:'
            ' empty response'.format(self.base_url))
        self._check_requests(jenkins_mock.call_args_list)
