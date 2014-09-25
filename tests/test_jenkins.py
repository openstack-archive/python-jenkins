import json
import sys
if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest

from mock import patch
import six

from tests.helper import jenkins


def get_mock_urlopen_return_value(a_dict=None):
    if a_dict is None:
        a_dict = {}
    return six.BytesIO(json.dumps(a_dict).encode('utf-8'))


class JenkinsTest(unittest.TestCase):

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

    def test_constructor_url_with_trailing_slash(self):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic dGVzdDp0ZXN0')
        self.assertEqual(j.crumb, None)

    def test_constructor_url_without_trailing_slash(self):
        j = jenkins.Jenkins('http://example.com', 'test', 'test')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic dGVzdDp0ZXN0')
        self.assertEqual(j.crumb, None)

    def test_constructor_without_user_or_password(self):
        j = jenkins.Jenkins('http://example.com')
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, None)
        self.assertEqual(j.crumb, None)

    def test_constructor_unicode_password(self):
        j = jenkins.Jenkins('http://example.com',
                            six.u('nonascii'),
                            six.u('\xe9\u20ac'))
        self.assertEqual(j.server, 'http://example.com/')
        self.assertEqual(j.auth, b'Basic bm9uYXNjaWk6w6nigqw=')
        self.assertEqual(j.crumb, None)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_config_encodes_job_name(self, jenkins_mock):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.get_job_config(u'Test Job')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/Test%20Job/config.xml')

    @patch('jenkins.urlopen')
    def test_maybe_add_crumb(self, jenkins_mock):
        jenkins_mock.return_value = get_mock_urlopen_return_value()
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        j.maybe_add_crumb(request)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/crumbIssuer/api/json')
        self.assertFalse(j.crumb)
        self.assertFalse('.crumb' in request.headers)

    @patch('jenkins.urlopen')
    def test_maybe_add_crumb__with_data(self, jenkins_mock):
        crumb_data = {
            "crumb": "dab177f483b3dd93483ef6716d8e792d",
            "crumbRequestField": ".crumb",
        }
        jenkins_mock.return_value = get_mock_urlopen_return_value(crumb_data)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        j.maybe_add_crumb(request)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/crumbIssuer/api/json')
        self.assertEqual(j.crumb, crumb_data)
        self.assertEqual(request.headers['.crumb'], crumb_data['crumb'])

    @patch('jenkins.urlopen')
    def test_jenkins_open(self, jenkins_mock):
        crumb_data = {
            "crumb": "dab177f483b3dd93483ef6716d8e792d",
            "crumbRequestField": ".crumb",
        }
        data = {'foo': 'bar'}
        jenkins_mock.side_effect = [
            get_mock_urlopen_return_value(crumb_data),
            get_mock_urlopen_return_value(data),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        response = j.jenkins_open(request)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/job/TestJob')
        self.assertEqual(response, json.dumps(data).encode('utf-8'))
        self.assertEqual(j.crumb, crumb_data)
        self.assertEqual(request.headers['.crumb'], crumb_data['crumb'])

    @patch('jenkins.urlopen')
    def test_jenkins_open__403(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        request = jenkins.Request('http://example.com/job/TestJob')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.jenkins_open(request, add_crumb=False)
        self.assertEqual(
            str(context_manager.exception),
            'Error in request.Possibly authentication failed [401]')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/job/TestJob')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_assert_job_exists__job_missing(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.assert_job_exists('NonExistent')
        self.assertEqual(
            str(context_manager.exception),
            'job[NonExistent] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_assert_job_exists__job_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.assert_job_exists('ExistingJob')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_job(self, jenkins_mock):
        config_xml = """
            <matrix-project>
                <actions/>
                <description>Foo</description>
            </matrix-project>"""
        jenkins_mock.side_effect = [
            None,
            None,
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.create_job(u'TestJob', config_xml)

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/createItem?name=TestJob')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_job__already_exists(self, jenkins_mock):
        config_xml = """
            <matrix-project>
                <actions/>
                <description>Foo</description>
            </matrix-project>"""
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.create_job(u'TestJob', config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] already exists')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_job__create_failed(self, jenkins_mock):
        config_xml = """
            <matrix-project>
                <actions/>
                <description>Foo</description>
            </matrix-project>"""
        jenkins_mock.side_effect = [
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.create_job(u'TestJob', config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/createItem?name=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[TestJob] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_reconfig_job(self, jenkins_mock):
        config_xml = """
            <matrix-project>
                <actions/>
                <description>Foo</description>
            </matrix-project>"""
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.reconfig_job(u'TestJob', config_xml)

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/config.xml')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(u'TestJob')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/build')
        self.assertEqual(build_info, {'foo': 'bar'})

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job__with_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(u'TestJob', token='some_token')

        self.assertEqual(jenkins_mock.call_args[0][0].get_full_url(),
                         u'http://example.com/job/TestJob/build?token=some_token')
        self.assertEqual(build_info, {'foo': 'bar'})

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job__with_parameters_and_token(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            {'foo': 'bar'},
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.build_job(
            u'TestJob',
            parameters={'when': 'now', 'why': 'because I felt like it'},
            token='some_token')

        self.assertTrue('token=some_token' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertTrue('when=now' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertTrue('why=because+I+felt+like+it' in jenkins_mock.call_args[0][0].get_full_url())
        self.assertEqual(build_info, {'foo': 'bar'})

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_build_job__job_doesnt_exist(self, jenkins_mock):
        jenkins_mock.side_effect = [None]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.build_job(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'no such job[TestJob]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_stop_build(self, jenkins_mock):
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.stop_build(u'TestJob', number=52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/52/stop')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_console_output(self, jenkins_mock):
        jenkins_mock.return_value = "build console output..."
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.get_build_console_output(u'TestJob', number=52)

        self.assertEqual(build_info, jenkins_mock.return_value)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/52/consoleText')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_console_output__None(self, jenkins_mock):
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_console_output__invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        console_output = j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(console_output, jenkins_mock.return_value)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_console_output__HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/52/consoleText',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_build_console_output(u'TestJob', number=52)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/52/consoleText')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info(self, jenkins_mock):
        build_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(build_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        build_info = j.get_build_info(u'TestJob', number=52)

        self.assertEqual(build_info, build_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/52/api/json?depth=0')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info__None(self, jenkins_mock):
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info__invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for job[TestJob] number[52]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_build_info__HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/api/json?depth=0',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_build_info(u'TestJob', number=52)
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] number[52] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_job_info(u'TestJob')

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?depth=0')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info__None(self, jenkins_mock):
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_info(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info__invalid_json(self, jenkins_mock):
        jenkins_mock.return_value = 'Invalid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_info(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for job[TestJob]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_info__HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/api/json?depth=0',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_info(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'job[TestJob] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_debug_job_info(self, jenkins_mock):
        job_info_to_return = {
            u'building': False,
            u'msg': u'test',
            u'revision': 66,
            u'user': u'unknown'
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.debug_job_info(u'TestJob')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?depth=0')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_jobs(self, jenkins_mock):
        jobs = {
            u'url': u'http://your_url_here/job/my_job/',
            u'color': u'blue',
            u'name': u'my_job',
        }
        job_info_to_return = {u'jobs': jobs}
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_jobs()

        self.assertEqual(job_info, jobs)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/api/json')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info(self, jenkins_mock):
        job_info_to_return = {
            u'jobs': {
                u'url': u'http://your_url_here/job/my_job/',
                u'color': u'blue',
                u'name': u'my_job',
            }
        }
        jenkins_mock.return_value = json.dumps(job_info_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_info = j.get_info()

        self.assertEqual(job_info, job_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/api/json')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_plugin_info_all(self, jenkins_mock):

        jenkins_mock.return_value = json.dumps(self.plugin_info_json)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        # expected to return a list of plugins
        plugin_info = j.get_plugin_info()
        self.assertEqual(plugin_info, self.plugin_info_json)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=2')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_plugin_info_shortname(self, jenkins_mock):

        jenkins_mock.return_value = json.dumps(self.plugin_info_json)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        # expected to return info on a single plugin
        plugin_info = j.get_plugin_info("mailer")
        self.assertEqual(plugin_info, self.plugin_info_json['plugins'][0])

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_plugin_info_longname(self, jenkins_mock):

        jenkins_mock.return_value = json.dumps(self.plugin_info_json)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        # expected to return info on a single plugin
        plugin_info = j.get_plugin_info("Jenkins Mailer Plugin")
        self.assertEqual(plugin_info, self.plugin_info_json['plugins'][0])

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_plugin_info_none(self, jenkins_mock):

        jenkins_mock.return_value = json.dumps(self.plugin_info_json)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        # expected not to find bogus so should return None
        plugin_info = j.get_plugin_info("bogus")
        self.assertEqual(plugin_info, None)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_plugin_info_depth(self, jenkins_mock):

        jenkins_mock.return_value = json.dumps(self.plugin_info_json)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        plugin_info = j.get_plugin_info(depth=1)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/pluginManager/api/json?depth=1')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob/api/json?depth=0',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__BadStatusLine(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.BadStatusLine('not a valid status line')
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Error communicating with server[http://example.com/]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_info__ValueError(self, jenkins_mock):
        jenkins_mock.return_value = 'not valid JSON'
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_info()
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/api/json')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for server[http://example.com/]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_copy_job(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob_2'}),
            json.dumps({'name': 'TestJob_2'}),
            json.dumps({'name': 'TestJob_2'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.copy_job(u'TestJob', u'TestJob_2')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/createItem'
            '?name=TestJob_2&mode=copy&from=TestJob')
        self.assertTrue(j.job_exists('TestJob_2'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_copy_job__create_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.copy_job(u'TestJob', u'TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/createItem'
            '?name=TestJob_2&mode=copy&from=TestJob')
        self.assertEqual(
            str(context_manager.exception),
            'create[TestJob_2] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_rename_job(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob_2'}),
            json.dumps({'name': 'TestJob_2'}),
            json.dumps({'name': 'TestJob_2'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.rename_job(u'TestJob', u'TestJob_2')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/TestJob/doRename?newName=TestJob_2')
        self.assertTrue(j.job_exists('TestJob_2'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_rename_job__rename_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.rename_job(u'TestJob', u'TestJob_2')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/TestJob/doRename?newName=TestJob_2')
        self.assertEqual(
            str(context_manager.exception),
            'rename[TestJob_2] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_job(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.delete_job(u'TestJob')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/TestJob/doDelete')
        self.assertFalse(j.job_exists('TestJob'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_job__delete_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.delete_job(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/TestJob/doDelete')
        self.assertEqual(
            str(context_manager.exception),
            'delete[TestJob] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_enable_job(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_job(u'TestJob')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/TestJob/enable')
        self.assertTrue(j.job_exists('TestJob'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_disable_job(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
            json.dumps({'name': 'TestJob'}),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_job(u'TestJob')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/job/TestJob/disable')
        self.assertTrue(j.job_exists('TestJob'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name(self, jenkins_mock):
        job_name_to_return = {u'name': 'TestJob'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_name = j.get_job_name(u'TestJob')

        self.assertEqual(job_name, 'TestJob')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?tree=name')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name__None(self, jenkins_mock):
        jenkins_mock.return_value = None
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        job_name = j.get_job_name(u'TestJob')

        self.assertEqual(job_name, None)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/job/TestJob/api/json?tree=name')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_job_name__unexpected_job_name(self, jenkins_mock):
        job_name_to_return = {u'name': 'not the right name'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_job_name(u'TestJob')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].get_full_url(),
            'http://example.com/job/TestJob/api/json?tree=name')
        self.assertEqual(
            str(context_manager.exception),
            'Jenkins returned an unexpected job name {0} '
            '(expected: {1})'.format(job_name_to_return['name'], 'TestJob'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_cancel_queue(self, jenkins_mock):
        job_name_to_return = {u'name': 'TestJob'}
        jenkins_mock.return_value = json.dumps(job_name_to_return)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.cancel_queue(52)

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/queue/item/52/cancelQueue')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_node_info(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        self.assertEqual(j.get_node_info('test_node'), node_info)
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_node_info__invalid_json(self, jenkins_mock):
        jenkins_mock.side_effect = [
            'Invalid JSON',
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_node_info('test_node')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for node[test_node]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_node_info__HTTPError(self, jenkins_mock):
        jenkins_mock.side_effect = jenkins.HTTPError(
            'http://example.com/job/TestJob',
            code=401,
            msg="basic auth failed",
            hdrs=[],
            fp=None)
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.get_node_info('test_node')
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')
        self.assertEqual(
            str(context_manager.exception),
            'node[test_node] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_assert_node_exists__node_missing(self, jenkins_mock):
        jenkins_mock.side_effect = [None]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.assert_node_exists('NonExistentNode')
        self.assertEqual(
            str(context_manager.exception),
            'node[NonExistentNode] does not exist')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_assert_node_exists__node_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'name': 'ExistingNode'})
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        j.assert_node_exists('ExistingNode')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_node(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.delete_node('test_node')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/computer/test_node/doDelete')
        self.assertFalse(j.node_exists('test_node'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_delete_node__delete_failed(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.delete_node('test_node')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url(),
            'http://example.com/computer/test_node/doDelete')
        self.assertEqual(
            str(context_manager.exception),
            'delete[test_node] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_node(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            None,
            None,
            json.dumps(node_info),
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.create_node('test_node', exclusive=True)

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url().split('?')[0],
            'http://example.com/computer/doCreateItem')
        self.assertTrue(j.node_exists('test_node'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_node__node_already_exists(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.create_node('test_node')
        self.assertEqual(
            str(context_manager.exception),
            'node[test_node] already exists')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_create_node__create_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            None,
            None,
            None,
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            j.create_node('test_node')
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].get_full_url().split('?')[0],
            'http://example.com/computer/doCreateItem')
        self.assertEqual(
            str(context_manager.exception),
            'create[test_node] failed')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_enable_node(self, jenkins_mock):
        expected_node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [
            json.dumps(expected_node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_node('test_node')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/' +
            'toggleOffline?offlineMessage=')

        expected_node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [json.dumps(expected_node_info)]
        node_info = j.get_node_info('test_node')
        self.assertEqual(node_info, expected_node_info)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_enable_node__offline_False(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.enable_node('test_node')

        # Node was not offline; so enable_node skips toggle
        # Last call to jenkins was to check status
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')

        expected_node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [json.dumps(expected_node_info)]
        node_info = j.get_node_info('test_node')
        self.assertEqual(node_info, expected_node_info)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_disable_node(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': False,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_node('test_node')

        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/' +
            'toggleOffline?offlineMessage=')

        expected_node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [json.dumps(expected_node_info)]
        node_info = j.get_node_info('test_node')
        self.assertEqual(node_info, expected_node_info)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_disable_node__offline_True(self, jenkins_mock):
        node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [
            json.dumps(node_info),
            None,
        ]
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        j.disable_node('test_node')

        # Node was already offline; so disable_node skips toggle
        # Last call to jenkins was to check status
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            'http://example.com/computer/test_node/api/json?depth=0')

        expected_node_info = {
            'displayName': 'nodes',
            'totalExecutors': 5,
            'offline': True,
        }
        jenkins_mock.side_effect = [json.dumps(expected_node_info)]
        node_info = j.get_node_info('test_node')
        self.assertEqual(node_info, expected_node_info)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_get_queue_info(self, jenkins_mock):
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
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')

        queue_info = j.get_queue_info()

        self.assertEqual(queue_info, queue_info_to_return['items'])
        self.assertEqual(
            jenkins_mock.call_args[0][0].get_full_url(),
            u'http://example.com/queue/api/json?depth=0')
