import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase


class JenkinsCancelQueueTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        job_name_to_return = {u'name': 'TestJob'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)

        self.j.cancel_queue(52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('queue/cancelItem?id=52'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open',
                  side_effect=jenkins.NotFoundException('not found'))
    def test_notfound(self, jenkins_mock):
        job_name_to_return = {u'name': 'TestJob'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)

        self.j.cancel_queue(52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('queue/cancelItem?id=52'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsQueueInfoTest(JenkinsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        queue_info_to_return = {
            'items': {
                u'task': {
                    u'url': u'http://your_url/job/my_job/',
                    u'color': u'aborted_anime',
                    u'name': u'my_job'
                },
                u'stuck': False,
                u'actions': [
                    {
                        u'causes': [
                            {
                                u'shortDescription': u'Started by timer',
                            },
                        ],
                    },
                ],
                u'buildable': False,
                u'params': u'',
                u'buildableStartMilliseconds': 1315087293316,
                u'why': u'Build #2,532 is already in progress (ETA:10 min)',
                u'blocked': True,
            }
        }
        jenkins_mock.return_value = json.dumps(queue_info_to_return)

        queue_info = self.j.get_queue_info()

        self.assertEqual(queue_info, queue_info_to_return['items'])
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('queue/api/json?depth=0'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsQueueItemTest(JenkinsTestBase):
    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        queue_item_to_return = {
            u'_class': u'hudson.model.Queue$LeftItem',
            u'actions': [{u'_class': u'hudson.model.CauseAction',
                          u'causes': [{u'_class': u'hudson.model.Cause$UserIdCause',
                                       u'shortDescription': u'Started by user Bob',
                                       u'userId': u'bsmith',
                                       u'userName': u'Bob'}]}],
            u'blocked': False,
            u'buildable': False,
            u'cancelled': False,
            u'executable': {u'_class': u'hudson.model.FreeStyleBuild',
                            u'number': 198,
                            u'url': u'http://your_url/job/my_job/198/'},
            u'id': 25,
            u'inQueueSince': 1507914654469,
            u'params': u'',
            u'stuck': False,
            u'task': {u'_class': u'hudson.model.FreeStyleProject',
                      u'color': u'red',
                      u'name': u'my_job',
                      u'url': u'http://your_url/job/my_job/'},
            u'url': u'queue/item/25/',
            u'why': None,
        }

        jenkins_mock.return_value = json.dumps(queue_item_to_return)

        queue_item = self.j.get_queue_item(25)

        self.assertEqual(queue_item, queue_item_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('queue/item/25/api/json?depth=0'))
        self._check_requests(jenkins_mock.call_args_list)
