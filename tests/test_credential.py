import json
from mock import patch

import jenkins
from tests.base import JenkinsTestBase


class JenkinsCredentialTestBase(JenkinsTestBase):
    config_xml = """<com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>
        <scope>GLOBAL</scope>
        <id>Test Credential</id>
        <username>Test-User</username>
        <password>secret123</password>
      </com.cloudbees.plugins.credentials.impl.UsernamePasswordCredentialsImpl>"""


class JenkinsGetTagTextTest(JenkinsCredentialTestBase):

    def test_simple(self):
        name_to_return = self.j._get_tag_text('id', self.config_xml)
        self.assertEqual('Test Credential', name_to_return)

    def test_failed(self):
        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j._get_tag_text('id', '<xml></xml>')
        self.assertEqual(str(context_manager.exception),
                         'tag[id] is invalidated')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j._get_tag_text('id', '<xml><id></id></xml>')
        self.assertEqual(str(context_manager.exception),
                         'tag[id] is invalidated')

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j._get_tag_text('id', '<xml><id>   </id></xml>')
        self.assertEqual(str(context_manager.exception),
                         'tag[id] is invalidated')


class JenkinsIsFolderTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_is_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
        ]
        self.assertTrue(self.j.is_folder('Test Folder'))

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_is_not_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'org.jenkinsci.plugins.workflow.job.WorkflowJob'}),
        ]
        self.assertFalse(self.j.is_folder('Test Job'))


class JenkinsAssertFolderTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_is_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
        ]
        self.j.assert_folder('Test Folder')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_is_not_folder(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'org.jenkinsci.plugins.workflow.job.WorkflowJob'}),
        ]
        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.assert_folder('Test Job')
        self.assertEqual(str(context_manager.exception),
                         'job[Test Job] is not a folder')


class JenkinsAssertCredentialTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_credential_missing(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            jenkins.NotFoundException()
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.assert_credential_exists('NonExistent', 'TestFoler')
        self.assertEqual(
            str(context_manager.exception),
            'credential[NonExistent] does not exist'
            ' in the domain[_] of [TestFoler]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_credential_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            json.dumps({'id': 'ExistingCredential'})
        ]
        self.j.assert_credential_exists('ExistingCredential', 'TestFoler')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsCredentialExistsTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_credential_missing(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            jenkins.NotFoundException()
        ]

        self.assertEqual(self.j.credential_exists('NonExistent', 'TestFolder'),
                         False)
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_credential_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            json.dumps({'id': 'ExistingCredential'})
        ]

        self.assertEqual(self.j.credential_exists('ExistingCredential',
                                                  'TestFolder'),
                         True)
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsGetCredentialInfoTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        credential_info_to_return = {'id': 'ExistingCredential'}
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            json.dumps(credential_info_to_return)
        ]

        credential_info = self.j.get_credential_info('ExistingCredential', 'TestFolder')

        self.assertEqual(credential_info, credential_info_to_return)
        self.assertEqual(
            jenkins_mock.call_args[0][0].url,
            self.make_url('job/TestFolder/credentials/store/folder/'
                          'domain/_/credential/ExistingCredential/api/json?depth=0'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_nonexistent(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            None,
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_credential_info('NonExistent', 'TestFolder')

        self.assertEqual(
            str(context_manager.exception),
            'credential[NonExistent] does not exist '
            'in the domain[_] of [TestFolder]')

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_invalid_json(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            '{invalid_json}'
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.get_credential_info('NonExistent', 'TestFolder')

        self.assertEqual(
            str(context_manager.exception),
            'Could not parse JSON info for credential[NonExistent]'
            ' in the domain[_] of [TestFolder]')


class JenkinsGetCredentialConfigTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_encodes_credential_name(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            None,
        ]
        self.j.get_credential_config(u'Test Credential', u'Test Folder')

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/domain/'
                          '_/credential/Test%20Credential/config.xml'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsCreateCredentialTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            jenkins.NotFoundException(),
            None,
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            json.dumps({'id': 'Test Credential'}),
        ]

        self.j.create_credential('Test Folder', self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/'
                          'domain/_/credential/Test%20Credential/api/json?depth=0'))

        self.assertEqual(
            jenkins_mock.call_args_list[2][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/'
                          'domain/_/createCredentials'))

        self.assertEqual(
            jenkins_mock.call_args_list[4][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/'
                          'domain/_/credential/Test%20Credential/api/json?depth=0'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_already_exists(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            json.dumps({'id': 'Test Credential'}),
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_credential('Test Folder', self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/'
                          'domain/_/credential/Test%20Credential/api/json?depth=0'))

        self.assertEqual(
            str(context_manager.exception),
            'credential[Test Credential] already exists'
            ' in the domain[_] of [Test Folder]')
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            jenkins.NotFoundException(),
            None,
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            None,
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.create_credential('Test Folder', self.config_xml)
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/'
                          'domain/_/credential/Test%20Credential/api/json?depth=0'))
        self.assertEqual(
            jenkins_mock.call_args_list[2][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/'
                          'folder/domain/_/createCredentials'))
        self.assertEqual(
            jenkins_mock.call_args_list[4][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/'
                          'domain/_/credential/Test%20Credential/api/json?depth=0'))
        self.assertEqual(
            str(context_manager.exception),
            'create[Test Credential] failed in the domain[_] of [Test Folder]')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsDeleteCredentialTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            True,
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            jenkins.NotFoundException(),
        ]

        self.j.delete_credential(u'Test Credential', 'TestFolder')

        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            self.make_url('job/TestFolder/credentials/store/folder/domain/'
                          '_/credential/Test%20Credential/config.xml'))
        self._check_requests(jenkins_mock.call_args_list)

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_failed(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'id': 'ExistingCredential'}),
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            json.dumps({'id': 'ExistingCredential'})
        ]

        with self.assertRaises(jenkins.JenkinsException) as context_manager:
            self.j.delete_credential(u'ExistingCredential', 'TestFolder')
        self.assertEqual(
            jenkins_mock.call_args_list[0][0][0].url,
            self.make_url('job/TestFolder/credentials/store/folder/'
                          'domain/_/credential/ExistingCredential/config.xml'))
        self.assertEqual(
            str(context_manager.exception),
            'delete credential[ExistingCredential] from '
            'domain[_] of [TestFolder] failed')
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsReconfigCredentialTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            json.dumps({'id': 'Test Credential'}),
            None
        ]

        self.j.reconfig_credential(u'Test Folder', self.config_xml)

        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/domain/'
                          '_/credential/Test%20Credential/api/json?depth=0'))
        self.assertEqual(
            jenkins_mock.call_args_list[2][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/domain/'
                          '_/credential/Test%20Credential/config.xml'))
        self._check_requests(jenkins_mock.call_args_list)


class JenkinsListCredentialConfigTest(JenkinsCredentialTestBase):

    @patch.object(jenkins.Jenkins, 'jenkins_open')
    def test_simple(self, jenkins_mock):
        credentials_to_return = [{'id': 'Test Credential'}]
        jenkins_mock.side_effect = [
            json.dumps({'_class': 'com.cloudbees.hudson.plugins.folder.Folder'}),
            json.dumps({'credentials': [{'id': 'Test Credential'}]}),
        ]
        credentials = self.j.list_credentials(u'Test Folder')
        self.assertEqual(credentials, credentials_to_return)
        self.assertEqual(
            jenkins_mock.call_args_list[1][0][0].url,
            self.make_url('job/Test%20Folder/credentials/store/folder/domain/'
                          '_/api/json?tree=credentials[id]'))
        self._check_requests(jenkins_mock.call_args_list)
