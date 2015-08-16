import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase


class JenkinsPluginsBase(JenkinsTestBase):

    plugin_info_json = {
        u"plugins":
        [
            {
                u"active": u'true',
                u"backupVersion": u'null',
                u"bundled": u'true',
                u"deleted": u'false',
                u"dependencies": [],
                u"downgradable": u'false',
                u"enabled": u'true',
                u"hasUpdate": u'true',
                u"longName": u"Jenkins Mailer Plugin",
                u"pinned": u'false',
                u"shortName": u"mailer",
                u"supportsDynamicLoad": u"MAYBE",
                u"url": u"http://wiki.jenkins-ci.org/display/JENKINS/Mailer",
                u"version": u"1.5"
            }
        ]
    }


class JenkinsPluginsInfoTest(JenkinsPluginsBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.return_value = json.dumps(self.plugin_info_json)

        # expected to return a list of plugins
        plugins_info = self.j.get_plugins_info()
        self.assertEqual(plugins_info, self.plugin_info_json['plugins'])
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=2')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        empty_plugin_info_json = {u"plugins": []}

        jenkins_mock.return_value = json.dumps(empty_plugin_info_json)

        plugins_info = self.j.get_plugins_info()
        self.assertEqual(plugins_info, [])
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_depth(self, jenkins_mock):
        jenkins_mock.return_value = json.dumps(self.plugin_info_json)

        self.j.get_plugins_info(depth=1)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=1')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_BadStatusLine(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.BadStatusLine('not a valid status line')

        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_plugins_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=2')
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'not valid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_plugins_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=2')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/pluginManager/api/json?depth=2',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)

        with self.assertRaises(jenkins.BadHTTPException) as context_manager:
            self.j.get_plugins_info(depth=52)
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsPluginInfoTest(JenkinsPluginsBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_shortname(self, jenkins_mock):
        jenkins_mock.return_value = json.dumps(self.plugin_info_json)

        # expected to return info on a single plugin
        plugin_info = self.j.get_plugin_info("mailer")
        self.assertEqual(plugin_info, self.plugin_info_json['plugins'][0])
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_longname(self, jenkins_mock):
        jenkins_mock.return_value = json.dumps(self.plugin_info_json)

        # expected to return info on a single plugin
        plugin_info = self.j.get_plugin_info("Jenkins Mailer Plugin")
        self.assertEqual(plugin_info, self.plugin_info_json['plugins'][0])
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_none(self, jenkins_mock):
        jenkins_mock.return_value = json.dumps(self.plugin_info_json)

        # expected not to find bogus so should return None
        plugin_info = self.j.get_plugin_info("bogus")
        self.assertEqual(plugin_info, None)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_depth(self, jenkins_mock):
        jenkins_mock.return_value = json.dumps(self.plugin_info_json)

        self.j.get_plugin_info('test', depth=1)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=1')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_BadStatusLine(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.BadStatusLine('not a valid status line')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_plugin_info('test')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=2')
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_return_invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'not valid JSON'

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_plugin_info('test')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=2')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_raise_HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/pluginManager/api/json?depth=2',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_plugin_info(u'TestPlugin', depth=52)
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')
        self._check_requests(jenkins_mock.call_args_list)
