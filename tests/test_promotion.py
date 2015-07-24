import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase

from six.moves.urllib.error import HTTPError


class JenkinsPromotionsTestBase(JenkinsTestBase):
    config_xml = """<hudson.plugins.promoted__builds.PromotionProcess>
    </hudson.plugins.promoted__builds.PromotionProcess>"""


class JenkinsGetPromotionNameTest(JenkinsPromotionsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        promotion_name_to_return = {u'name': 'Test Promotion'}
        jenkins_mock.return_value = json.dumps(promotion_name_to_return)

        promotion_name = self.j.get_promotion_name(u'Test Promotion',
                                                   u'Test Job')

        self.assertEqual(promotion_name, 'Test Promotion')
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/promotion/process/'
                          'Test%20Promotion/api/json?tree=name'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()

        promotion_name = self.j.get_promotion_name(u'TestPromotion',
                                                   u'Test Job')

        self.assertEqual(promotion_name, None)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/promotion/process/'
                          'TestPromotion/api/json?tree=name'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_unexpected_promotion_name(self, jenkins_mock):
        promotion_name_to_return = {u'name': 'not the right name'}
        jenkins_mock.return_value = json.dumps(promotion_name_to_return)

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_promotion_name(u'TestPromotion', u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            self.make_url('job/TestJob/promotion/process/TestPromotion'
                          '/api/json?tree=name'))
        self.assertEqual(
            str(context_manager.exception),
            'Jenkins returned an unexpected promotion name {0} '
            '(expected: {1})'.format(promotion_name_to_return['name'],
                                     'TestPromotion'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsAssertPromotionTest(JenkinsPromotionsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_promotion_missing(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.assert_promotion_exists('NonExistent', 'TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'promotion[NonExistent] does not exist for job[TestJob]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_promotion_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingPromotion'}),
        ]
        self.j.assert_promotion_exists('ExistingPromotion', 'TestJob')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsPromotionExistsTest(JenkinsPromotionsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_promotion_missing(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.NotFoundException()

        self.assertEqual(self.j.promotion_exists('NonExistent', 'TestJob'),
                         False)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_promotion_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingPromotion'}),
        ]

        self.assertEqual(self.j.promotion_exists('ExistingPromotion',
                                                 'TestJob'),
                         True)
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetPromotionsTest(JenkinsPromotionsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        promotions = {
            u'url': (u'http://your_url_here/jobs/TestJob/promotions'
                     u'/my_promotion/'),
            u'name': u'my_promotion',
        }
        promotion_info_to_return = {u'processes': promotions}
        jenkins_mock.return_value = json.dumps(promotion_info_to_return)

        promotion_info = self.j.get_promotions('TestJob')

        self.assertEqual(promotion_info, promotions)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/TestJob/promotion/api/json?depth=0'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_nonexistent(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            HTTPError,
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_promotions('TestJob')

        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = '{invalid_json}'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_promotions('TestJob')

        self.assertEqual(
            str(context_manager.exception),
            "Could not parse JSON info for promotions of job[TestJob]")


class JenkinsDeletePromotionTest(JenkinsPromotionsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            jenkins.NotFoundException(),
        ]

        self.j.delete_promotion(u'Test Promotion', 'TestJob')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            self.make_url('job/TestJob/promotion/process/'
                          'Test%20Promotion/doDelete'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestPromotion'}),
            json.dumps({'name': 'TestPromotion'}),
            json.dumps({'name': 'TestPromotion'}),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.delete_promotion(u'TestPromotion', 'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            self.make_url('job/TestJob/promotion/process/'
                          'TestPromotion/doDelete'))
        self.assertEqual(
            str(context_manager.exception),
            'delete[TestPromotion] from job[TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsCreatePromotionTest(JenkinsPromotionsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            jenkins.NotFoundException(),
            None,
            json.dumps({'name': 'Test Promotion'}),
        ]

        self.j.create_promotion(u'Test Promotion', 'Test Job', self.config_xml)

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('job/Test%20Job/promotion/'
                          'createProcess?name=Test%20Promotion'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_already_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestPromotion'}),
            None,
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_promotion(u'TestPromotion', 'TestJob',
                                    self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            self.make_url('job/TestJob/promotion/process/'
                          'TestPromotion/api/json?tree=name'))
        self.assertEqual(
            str(context_manager.exception),
            'promotion[TestPromotion] already exists at job[TestJob]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            jenkins.NotFoundException(),
            None,
            jenkins.NotFoundException(),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_promotion(u'TestPromotion', 'TestJob',
                                    self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            self.make_url('job/TestJob/promotion/process/'
                          'TestPromotion/api/json?tree=name'))
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('job/TestJob/promotion/'
                          'createProcess?name=TestPromotion'))
        self.assertEqual(
            str(context_manager.exception),
            'create[TestPromotion] at job[TestJob] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsReconfigPromotionTest(JenkinsPromotionsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'Test Promotion'}),
            None,
        ]

        self.j.reconfig_promotion(u'Test Promotion', u'Test Job',
                                  self.config_xml)

        self.assertEqual(jenkins_mock.call_args[0][0].url,
                         self.make_url('job/Test%20Job/promotion/process/'
                                       'Test%20Promotion/config.xml'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetPromotionConfigTest(JenkinsPromotionsTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_encodes_promotion_name(self, jenkins_mock):
        self.j.get_promotion_config(u'Test Promotion', u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/Test%20Job/promotion/process/'
                          'Test%20Promotion/config.xml'))
        self._check_requests(jenkins_mock.call_args_list)
