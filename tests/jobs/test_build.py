# -*- coding: utf-8 -*-
from mock import patch

import jenkins
from six.moves.urllib.parse import quote
from tests.helper import build_response_mock
from tests.jobs.base import JenkinsJobsTestBase


class JenkinsBuildJobTest(JenkinsJobsTestBase):

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_simple(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(
            302, {}, headers={'Location': self.make_url('/queue/item/25/')})

        queue_id = self.j.build_job(u'Test Jøb')

        self.assertEqual(session_send_mock.call_args[0][1].url,
                         self.make_url(quote(u'job/Test Jøb/build'.encode('utf8'))))
        self.assertEqual(queue_id, 25)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_assert_no_location(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(302, {})

        with self.assertRaises(jenkins.EmptyResponseException) as context_mgr:
            self.j.build_job(u'Test Job')

        self.assertEqual(
            str(context_mgr.exception),
            "Header 'Location' not found in response from server[{0}]".format(
                self.make_url('')))

    @patch.object(jenkins.Jenkins, 'maybe_add_crumb')
    @patch('jenkins.requests.Session.send', autospec=True)
    def test_simple_no_content_lenght(self, session_send_mock,
                                      maybe_add_crumb_mock):
        maybe_add_crumb_mock.return_value = None
        session_send_mock.return_value = build_response_mock(
            201, None, add_content_length=False,
            headers={'Location': self.make_url('/queue/item/25/')})

        queue_id = self.j.build_job(u'Test Job')

        self.assertEqual(session_send_mock.call_args[0][1].url,
                         self.make_url('job/Test%20Job/build'))
        self.assertEqual(queue_id, 25)

    @patch.object(jenkins.Jenkins, 'maybe_add_crumb')
    @patch('jenkins.requests.Session.send', autospec=True)
    def test_assert_no_content_lenght_no_location(self, session_send_mock,
                                                  maybe_add_crumb_mock):
        maybe_add_crumb_mock.return_value = None
        session_send_mock.return_value = build_response_mock(
            201, None, add_content_length=False)

        with self.assertRaises(jenkins.EmptyResponseException) as context_mgr:
            self.j.build_job(u'Test Job')

        self.assertEqual(
            str(context_mgr.exception),
            "Header 'Location' not found in response from server[{0}]".format(
                self.make_url('')))

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_in_folder(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(
            302, {}, headers={'Location': self.make_url('/queue/item/25/')})

        queue_id = self.j.build_job(u'a Folder/Test Job')

        self.assertEqual(session_send_mock.call_args[0][1].url,
                         self.make_url('job/a%20Folder/job/Test%20Job/build'))
        self.assertEqual(queue_id, 25)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_with_token(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(
            302, {}, headers={'Location': self.make_url('/queue/item/25/')})

        queue_id = self.j.build_job(u'TestJob', token='some_token')

        self.assertEqual(session_send_mock.call_args[0][1].url,
                         self.make_url('job/TestJob/build?token=some_token'))
        self.assertEqual(queue_id, 25)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_in_folder_with_token(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(
            302, {}, headers={'Location': self.make_url('/queue/item/25/')})

        queue_id = self.j.build_job(u'a Folder/TestJob', token='some_token')

        self.assertEqual(session_send_mock.call_args[0][1].url,
                         self.make_url('job/a%20Folder/job/TestJob/build?token=some_token'))
        self.assertEqual(queue_id, 25)

    @patch('jenkins.requests.Session.send', autospec=True)
    def test_with_parameters_and_token(self, session_send_mock):
        session_send_mock.return_value = build_response_mock(
            302, {}, headers={'Location': self.make_url('/queue/item/25/')})

        queue_id = self.j.build_job(
            u'TestJob',
            parameters={'when': 'now', 'why': 'because I felt like it'},
            token='some_token')

        self.assertTrue('token=some_token' in session_send_mock.call_args[0][1].url)
        self.assertTrue('when=now' in session_send_mock.call_args[0][1].url)
        self.assertTrue('why=because+I+felt+like+it' in session_send_mock.call_args[0][1].url)
        self.assertEqual(queue_id, 25)
