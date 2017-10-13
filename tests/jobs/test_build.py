from mock import patch, Mock
import six

from tests.jobs.base import JenkinsJobsTestBase


class JenkinsBuildJobTest(JenkinsJobsTestBase):

    def mock_response(self):
        """ Return a fake response suitable for returning from urlopen(). """
        mock_response = Mock()
        location = self.make_url('/queue/item/25/')
        if six.PY2:
            config = {'info.return_value.getheader.return_value': location}
        if six.PY3:
            config = {'getheader.return_value': location}
        mock_response.configure_mock(**config)
        mock_response.read.return_value = ['{}', '']
        return mock_response

    @patch('jenkins.urlopen')
    def test_simple(self, urlopen_mock):
        urlopen_mock.side_effect = [None, self.mock_response()]

        build_info = self.j.build_job(u'Test Job')

        self.assertEqual(urlopen_mock.call_args[0][0].get_full_url(),
                         self.make_url('job/Test%20Job/build'))
        self.assertEqual(build_info, 25)
        self._check_requests(urlopen_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_in_folder(self, urlopen_mock):
        urlopen_mock.side_effect = [None, self.mock_response()]

        build_info = self.j.build_job(u'a Folder/Test Job')

        self.assertEqual(urlopen_mock.call_args[0][0].get_full_url(),
                         self.make_url('job/a%20Folder/job/Test%20Job/build'))
        self.assertEqual(build_info, 25)
        self._check_requests(urlopen_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_with_token(self, urlopen_mock):
        urlopen_mock.side_effect = [None, self.mock_response()]

        build_info = self.j.build_job(u'TestJob', token='some_token')

        self.assertEqual(urlopen_mock.call_args[0][0].get_full_url(),
                         self.make_url('job/TestJob/build?token=some_token'))
        self.assertEqual(build_info, 25)
        self._check_requests(urlopen_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_in_folder_with_token(self, urlopen_mock):
        urlopen_mock.side_effect = [None, self.mock_response()]

        build_info = self.j.build_job(u'a Folder/TestJob', token='some_token')

        self.assertEqual(urlopen_mock.call_args[0][0].get_full_url(),
                         self.make_url('job/a%20Folder/job/TestJob/build?token=some_token'))
        self.assertEqual(build_info, 25)
        self._check_requests(urlopen_mock.call_args_list)

    @patch('jenkins.urlopen')
    def test_with_parameters_and_token(self, urlopen_mock):
        urlopen_mock.side_effect = [None, self.mock_response()]

        build_info = self.j.build_job(
            u'TestJob',
            parameters={'when': 'now', 'why': 'because I felt like it'},
            token='some_token')

        self.assertTrue('token=some_token' in urlopen_mock.call_args[0][0].get_full_url())
        self.assertTrue('when=now' in urlopen_mock.call_args[0][0].get_full_url())
        self.assertTrue('why=because+I+felt+like+it' in urlopen_mock.call_args[0][0].get_full_url())
        self.assertEqual(build_info, 25)
        self._check_requests(urlopen_mock.call_args_list)
