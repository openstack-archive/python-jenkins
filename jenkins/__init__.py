#!/usr/bin/env python
# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# 'AS IS' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Authors:
# Ken Conley <kwc@willowgarage.com>
# James Page <james.page@canonical.com>
# Tully Foote <tfoote@willowgarage.com>
# Matthew Gertner <matthew.gertner@gmail.com>

'''
.. module:: jenkins
    :platform: Unix, Windows
    :synopsis: Python API to interact with Jenkins
    :noindex:

See examples at :doc:`examples`
'''

import json
import logging
import os
import re
import socket
import sys
import time
import warnings

import multi_key_dict
import requests
import requests.exceptions as req_exc
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from six.moves.http_client import BadStatusLine
from six.moves.urllib.error import URLError
from six.moves.urllib.parse import quote, urlencode, urljoin, urlparse
import xml.etree.ElementTree as ET

from jenkins import plugins

try:
    import requests_kerberos
except ImportError:
    requests_kerberos = None

# Set default logging handler to avoid "No handler found" warnings.
try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass


logging.getLogger(__name__).addHandler(NullHandler())

if sys.version_info < (2, 7, 0):
    warnings.warn("Support for python 2.6 is deprecated and will be removed.")


LAUNCHER_SSH = 'hudson.plugins.sshslaves.SSHLauncher'
LAUNCHER_COMMAND = 'hudson.slaves.CommandLauncher'
LAUNCHER_JNLP = 'hudson.slaves.JNLPLauncher'
LAUNCHER_WINDOWS_SERVICE = 'hudson.os.windows.ManagedWindowsServiceLauncher'
DEFAULT_HEADERS = {'Content-Type': 'text/xml; charset=utf-8'}

# REST Endpoints
INFO = 'api/json'
PLUGIN_INFO = 'pluginManager/api/json?depth=%(depth)s'
CRUMB_URL = 'crumbIssuer/api/json'
WHOAMI_URL = 'me/api/json?depth=%(depth)s'
JOBS_QUERY = '?tree=%s'
JOBS_QUERY_TREE = 'jobs[url,color,name,%s]'
JOB_INFO = '%(folder_url)sjob/%(short_name)s/api/json?depth=%(depth)s'
JOB_NAME = '%(folder_url)sjob/%(short_name)s/api/json?tree=name'
ALL_BUILDS = '%(folder_url)sjob/%(short_name)s/api/json?tree=allBuilds[number,url]'
Q_INFO = 'queue/api/json?depth=0'
Q_ITEM = 'queue/item/%(number)d/api/json?depth=%(depth)s'
CANCEL_QUEUE = 'queue/cancelItem?id=%(id)s'
CREATE_JOB = '%(folder_url)screateItem?name=%(short_name)s'  # also post config.xml
CONFIG_JOB = '%(folder_url)sjob/%(short_name)s/config.xml'
DELETE_JOB = '%(folder_url)sjob/%(short_name)s/doDelete'
ENABLE_JOB = '%(folder_url)sjob/%(short_name)s/enable'
DISABLE_JOB = '%(folder_url)sjob/%(short_name)s/disable'
SET_JOB_BUILD_NUMBER = '%(folder_url)sjob/%(short_name)s/nextbuildnumber/submit'
COPY_JOB = '%(from_folder_url)screateItem?name=%(to_short_name)s&mode=copy&from=%(from_short_name)s'
RENAME_JOB = '%(from_folder_url)sjob/%(from_short_name)s/doRename?newName=%(to_short_name)s'
BUILD_JOB = '%(folder_url)sjob/%(short_name)s/build'
STOP_BUILD = '%(folder_url)sjob/%(short_name)s/%(number)s/stop'
BUILD_WITH_PARAMS_JOB = '%(folder_url)sjob/%(short_name)s/buildWithParameters'
BUILD_INFO = '%(folder_url)sjob/%(short_name)s/%(number)d/api/json?depth=%(depth)s'
BUILD_CONSOLE_OUTPUT = '%(folder_url)sjob/%(short_name)s/%(number)d/consoleText'
BUILD_ENV_VARS = '%(folder_url)sjob/%(short_name)s/%(number)d/injectedEnvVars/api/json' + \
    '?depth=%(depth)s'
BUILD_TEST_REPORT = '%(folder_url)sjob/%(short_name)s/%(number)d/testReport/api/json' + \
    '?depth=%(depth)s'
DELETE_BUILD = '%(folder_url)sjob/%(short_name)s/%(number)s/doDelete'
WIPEOUT_JOB_WORKSPACE = '%(folder_url)sjob/%(short_name)s/doWipeOutWorkspace'
NODE_LIST = 'computer/api/json?depth=%(depth)s'
CREATE_NODE = 'computer/doCreateItem'
DELETE_NODE = 'computer/%(name)s/doDelete'
NODE_INFO = 'computer/%(name)s/api/json?depth=%(depth)s'
NODE_TYPE = 'hudson.slaves.DumbSlave$DescriptorImpl'
TOGGLE_OFFLINE = 'computer/%(name)s/toggleOffline?offlineMessage=%(msg)s'
CONFIG_NODE = 'computer/%(name)s/config.xml'
VIEW_NAME = '%(folder_url)sview/%(short_name)s/api/json?tree=name'
VIEW_JOBS = 'view/%(name)s/api/json?tree=jobs[url,color,name]'
CREATE_VIEW = '%(folder_url)screateView?name=%(short_name)s'
CONFIG_VIEW = '%(folder_url)sview/%(short_name)s/config.xml'
DELETE_VIEW = '%(folder_url)sview/%(short_name)s/doDelete'
SCRIPT_TEXT = 'scriptText'
NODE_SCRIPT_TEXT = 'computer/%(node)s/scriptText'
PROMOTION_NAME = '%(folder_url)sjob/%(short_name)s/promotion/process/%(name)s/api/json?tree=name'
PROMOTION_INFO = '%(folder_url)sjob/%(short_name)s/promotion/api/json?depth=%(depth)s'
DELETE_PROMOTION = '%(folder_url)sjob/%(short_name)s/promotion/process/%(name)s/doDelete'
CREATE_PROMOTION = '%(folder_url)sjob/%(short_name)s/promotion/createProcess?name=%(name)s'
CONFIG_PROMOTION = '%(folder_url)sjob/%(short_name)s/promotion/process/%(name)s/config.xml'
LIST_CREDENTIALS = '%(folder_url)sjob/%(short_name)s/credentials/store/folder/' \
                    'domain/%(domain_name)s/api/json?tree=credentials[id]'
CREATE_CREDENTIAL = '%(folder_url)sjob/%(short_name)s/credentials/store/folder/' \
                    'domain/%(domain_name)s/createCredentials'
CONFIG_CREDENTIAL = '%(folder_url)sjob/%(short_name)s/credentials/store/folder/' \
                    'domain/%(domain_name)s/credential/%(name)s/config.xml'
CREDENTIAL_INFO = '%(folder_url)sjob/%(short_name)s/credentials/store/folder/' \
                    'domain/%(domain_name)s/credential/%(name)s/api/json?depth=0'
QUIET_DOWN = 'quietDown'

# for testing only
EMPTY_CONFIG_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<project>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class='jenkins.scm.NullSCM'/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class='vector'/>
  <concurrentBuild>false</concurrentBuild>
  <builders/>
  <publishers/>
  <buildWrappers/>
</project>'''

# for testing only
EMPTY_FOLDER_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<com.cloudbees.hudson.plugins.folder.Folder plugin="cloudbees-folder@6.1.2">
  <actions/>
  <description></description>
  <properties/>
  <folderViews/>
  <healthMetrics/>
</com.cloudbees.hudson.plugins.folder.Folder>'''

# for testing only
RECONFIG_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<project>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class='jenkins.scm.NullSCM'/>
  <canRoam>true</canRoam>
  <disabled>false</disabled>
  <blockBuildWhenUpstreamBuilding>false</blockBuildWhenUpstreamBuilding>
  <triggers class='vector'/>
  <concurrentBuild>false</concurrentBuild>
  <builders>
    <jenkins.tasks.Shell>
      <command>export FOO=bar</command>
    </jenkins.tasks.Shell>
  </builders>
  <publishers/>
  <buildWrappers/>
</project>'''

# for testing only
EMPTY_VIEW_CONFIG_XML = '''<?xml version="1.0" encoding="UTF-8"?>
<hudson.model.ListView>
  <name>EMPTY</name>
  <filterExecutors>false</filterExecutors>
  <filterQueue>false</filterQueue>
  <properties class="hudson.model.View$PropertyList"/>
  <jobNames>
    <comparator class="hudson.util.CaseInsensitiveComparator"/>
  </jobNames>
  <jobFilters/>
  <columns>
    <hudson.views.StatusColumn/>
    <hudson.views.WeatherColumn/>
    <hudson.views.JobColumn/>
    <hudson.views.LastSuccessColumn/>
    <hudson.views.LastFailureColumn/>
    <hudson.views.LastDurationColumn/>
    <hudson.views.BuildButtonColumn/>
  </columns>
</hudson.model.ListView>'''

# for testing only
EMPTY_PROMO_CONFIG_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<hudson.plugins.promoted__builds.PromotionProcess>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <canRoam>false</canRoam>
  <triggers/>
  <conditions/>
  <icon>star-gold</icon>
  <buildSteps/>
</hudson.plugins.promoted__builds.PromotionProcess>'''

# for testing only
PROMO_RECONFIG_XML = '''<?xml version='1.0' encoding='UTF-8'?>
<hudson.plugins.promoted__builds.PromotionProcess>
  <keepDependencies>false</keepDependencies>
  <properties/>
  <scm class="hudson.scm.NullSCM"/>
  <triggers/>
  <icon>star-green</icon>
  <buildSteps>
    <hudson.tasks.Shell>
      <command>ls -l</command>
    </hudson.tasks.Shell>
  </buildSteps>
</hudson.plugins.promoted__builds.PromotionProcess>
'''


class JenkinsException(Exception):
    '''General exception type for jenkins-API-related failures.'''
    pass


class NotFoundException(JenkinsException):
    '''A special exception to call out the case of receiving a 404.'''
    pass


class EmptyResponseException(JenkinsException):
    '''A special exception to call out the case receiving an empty response.'''
    pass


class BadHTTPException(JenkinsException):
    '''A special exception to call out the case of a broken HTTP response.'''
    pass


class TimeoutException(JenkinsException):
    '''A special exception to call out in the case of a socket timeout.'''


class WrappedSession(requests.Session):
    """A wrapper for requests.Session to override 'verify' property, ignoring REQUESTS_CA_BUNDLE environment variable.

    This is a workaround for https://github.com/kennethreitz/requests/issues/3829 (will be fixed in requests 3.0.0)
    """

    def merge_environment_settings(self, url, proxies, stream, verify, *args,
                                   **kwargs):
        if self.verify is False:
            verify = False

        return super(WrappedSession, self).merge_environment_settings(url,
                                                                      proxies,
                                                                      stream,
                                                                      verify,
                                                                      *args,
                                                                      **kwargs)


class Jenkins(object):
    _timeout_warning_issued = False

    def __init__(self, url, username=None, password=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        '''Create handle to Jenkins instance.

        All methods will raise :class:`JenkinsException` on failure.

        :param url: URL of Jenkins server, ``str``
        :param username: Server username, ``str``
        :param password: Server password, ``str``
        :param timeout: Server connection timeout in secs (default: not set), ``int``
        '''
        if url[-1] == '/':
            self.server = url
        else:
            self.server = url + '/'

        self._auths = [('anonymous', None)]
        self._auth_resolved = False
        if username is not None and password is not None:
            self._auths[0] = (
                'basic',
                requests.auth.HTTPBasicAuth(
                    username.encode('utf-8'), password.encode('utf-8'))
            )

        if requests_kerberos is not None:
            self._auths.append(
                ('kerberos', requests_kerberos.HTTPKerberosAuth())
            )

        self.auth = None
        self.crumb = None
        self.timeout = timeout
        self._session = WrappedSession()

        extra_headers = os.environ.get("JENKINS_API_EXTRA_HEADERS", "")
        if extra_headers:
            logging.warning("JENKINS_API_EXTRA_HEADERS adds these HTTP headers: %s", extra_headers.split("\n"))
        for token in extra_headers.split("\n"):
            if ":" in token:
                header, value = token.split(":", 1)
                self._session.headers[header] = value.strip()

        if os.getenv('PYTHONHTTPSVERIFY', '1') == '0':
            logging.debug('PYTHONHTTPSVERIFY=0 detected so we will '
                          'disable requests library SSL verification to keep '
                          'compatibility with older versions.')
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            self._session.verify = False

    def _get_encoded_params(self, params):
        for k, v in params.items():
            if k in ["name", "msg", "short_name", "from_short_name",
                     "to_short_name", "folder_url", "from_folder_url", "to_folder_url"]:
                params[k] = quote(v.encode('utf8'))
        return params

    def _build_url(self, format_spec, variables=None):

        if variables:
            url_path = format_spec % self._get_encoded_params(variables)
        else:
            url_path = format_spec

        return str(urljoin(self.server, url_path))

    def maybe_add_crumb(self, req):
        # We don't know yet whether we need a crumb
        if self.crumb is None:
            try:
                response = self.jenkins_open(requests.Request(
                    'GET', self._build_url(CRUMB_URL)), add_crumb=False)
            except (NotFoundException, EmptyResponseException):
                self.crumb = False
            else:
                self.crumb = json.loads(response)
        if self.crumb:
            req.headers[self.crumb['crumbRequestField']] = self.crumb['crumb']

    def _maybe_add_auth(self):

        if self._auth_resolved:
            return

        if len(self._auths) == 1:
            # If we only have one auth mechanism specified, just require it
            self._session.auth = self._auths[0][1]
        else:
            # Attempt the list of auth mechanisms and keep the first that works
            # otherwise default to the first one in the list (last popped).
            # This is a hack to allow the transparent use of kerberos to work
            # in future, we should require explicit request to use kerberos
            failures = []
            for name, auth in reversed(self._auths):
                try:
                    self.jenkins_open(
                        requests.Request('GET', self._build_url(INFO),
                                         auth=auth),
                        add_crumb=False, resolve_auth=False)
                    self._session.auth = auth
                    break
                except TimeoutException:
                    raise
                except Exception as exc:
                    # assume authentication failure
                    failures.append("auth(%s) %s" % (name, exc))
                    continue
            else:
                raise JenkinsException(
                    'Unable to authenticate with any scheme:\n%s'
                    % '\n'.join(failures))

        self._auth_resolved = True
        self.auth = self._session.auth

    def _add_missing_builds(self, data):
        """Query Jenkins to get all builds of a job.

        The Jenkins API only fetches the first 100 builds, with no
        indicator that there are more to be fetched. This fetches more
        builds where necessary to get all builds of a given job.

        Much of this code borrowed from
        https://github.com/salimfadhley/jenkinsapi/blob/master/jenkinsapi/job.py,
        which is MIT licensed.
        """
        if not data.get("builds"):
            return data
        oldest_loaded_build_number = data["builds"][-1]["number"]
        if not data['firstBuild']:
            first_build_number = oldest_loaded_build_number
        else:
            first_build_number = data["firstBuild"]["number"]
        all_builds_loaded = (oldest_loaded_build_number == first_build_number)
        if all_builds_loaded:
            return data
        folder_url, short_name = self._get_job_folder(data["name"])
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(ALL_BUILDS, locals())
        ))
        if response:
            data["builds"] = json.loads(response)["allBuilds"]
        else:
            raise JenkinsException('Could not fetch all builds from job[%s]' %
                                   data["name"])
        return data

    def get_job_info(self, name, depth=0, fetch_all_builds=False):
        '''Get job information dictionary.

        :param name: Job name, ``str``
        :param depth: JSON depth, ``int``
        :param fetch_all_builds: If true, all builds will be retrieved
                                 from Jenkins. Otherwise, Jenkins will
                                 only return the most recent 100
                                 builds. This comes at the expense of
                                 an additional API call which may
                                 return significant amounts of
                                 data. ``bool``
        :returns: dictionary of job information
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(JOB_INFO, locals())
            ))
            if response:
                if fetch_all_builds:
                    return self._add_missing_builds(json.loads(response))
                else:
                    return json.loads(response)
            else:
                raise JenkinsException('job[%s] does not exist' % name)
        except (req_exc.HTTPError, NotFoundException):
            raise JenkinsException('job[%s] does not exist' % name)
        except ValueError:
            raise JenkinsException(
                "Could not parse JSON info for job[%s]" % name)

    def get_job_info_regex(self, pattern, depth=0, folder_depth=0,
                           folder_depth_per_request=10):
        '''Get a list of jobs information that contain names which match the
           regex pattern.

        :param pattern: regex pattern, ``str``
        :param depth: JSON depth, ``int``
        :param folder_depth: folder level depth to search ``int``
        :param folder_depth_per_request: Number of levels to fetch at once,
            ``int``. See :func:`get_all_jobs`.
        :returns: List of jobs info, ``list``
        '''
        result = []
        jobs = self.get_all_jobs(folder_depth=folder_depth,
                                 folder_depth_per_request=folder_depth_per_request)
        for job in jobs:
            if re.search(pattern, job['name']):
                result.append(self.get_job_info(job['name'], depth=depth))

        return result

    def get_job_name(self, name):
        '''Return the name of a job using the API.

        That is roughly an identity method which can be used to quickly verify
        a job exists or is accessible without causing too much stress on the
        server side.

        :param name: Job name, ``str``
        :returns: Name of job or None
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(JOB_NAME, locals())
            ))
        except NotFoundException:
            return None
        else:
            actual = json.loads(response)['name']
            if actual != short_name:
                raise JenkinsException(
                    'Jenkins returned an unexpected job name %s '
                    '(expected: %s)' % (actual, name))
            return actual

    def debug_job_info(self, job_name):
        '''Print out job info in more readable format.'''
        for k, v in self.get_job_info(job_name).items():
            print(k, v)

    def _response_handler(self, response):
        '''Handle response objects'''

        # raise exceptions if occurred
        response.raise_for_status()

        headers = response.headers
        if (headers.get('content-length') is None and
                headers.get('transfer-encoding') is None and
                headers.get('location') is None and
                (response.content is None or len(response.content) <= 0)):
            # response body should only exist if one of these is provided
            raise EmptyResponseException(
                "Error communicating with server[%s]: "
                "empty response" % self.server)

        # Response objects will automatically return unicode encoded
        # when accessing .text property
        return response

    def _request(self, req):

        r = self._session.prepare_request(req)
        # requests.Session.send() does not honor env settings by design
        # see https://github.com/requests/requests/issues/2807
        _settings = self._session.merge_environment_settings(
            r.url, {}, None, self._session.verify, None)
        _settings['timeout'] = self.timeout
        return self._session.send(r, **_settings)

    def jenkins_open(self, req, add_crumb=True, resolve_auth=True):
        '''Return the HTTP response body from a ``requests.Request``.

        :returns: ``str``
        '''
        return self.jenkins_request(req, add_crumb, resolve_auth).text

    def jenkins_request(self, req, add_crumb=True, resolve_auth=True):
        '''Utility routine for opening an HTTP request to a Jenkins server.

        :param req: A ``requests.Request`` to submit.
        :param add_crumb: If True, try to add a crumb header to this ``req``
                          before submitting. Defaults to ``True``.
        :param resolve_auth: If True, maybe add authentication. Defaults to
                             ``True``.
        :returns: A ``requests.Response`` object.
        '''
        try:
            if resolve_auth:
                self._maybe_add_auth()
            if add_crumb:
                self.maybe_add_crumb(req)

            return self._response_handler(
                self._request(req))

        except req_exc.HTTPError as e:
            # Jenkins's funky authentication means its nigh impossible to
            # distinguish errors.
            if e.response.status_code in [401, 403, 500]:
                msg = 'Error in request. ' + \
                      'Possibly authentication failed [%s]: %s' % (
                          e.response.status_code, e.response.reason)
                if e.response.text:
                    msg += '\n' + e.response.text
                raise JenkinsException(msg)
            elif e.response.status_code == 404:
                raise NotFoundException('Requested item could not be found')
            else:
                raise
        except req_exc.Timeout as e:
            raise TimeoutException('Error in request: %s' % (e))
        except URLError as e:
            # python 2.6 compatibility to ensure same exception raised
            # since URLError wraps a socket timeout on python 2.6.
            if str(e.reason) == "timed out":
                raise TimeoutException('Error in request: %s' % (e.reason))
            raise JenkinsException('Error in request: %s' % (e.reason))

    def get_queue_item(self, number, depth=0):
        '''Get information about a queued item (to-be-created job).

        The returned dict will have a "why" key if the queued item is still
        waiting for an executor.

        The returned dict will have an "executable" key if the queued item is
        running on an executor, or has completed running. Use this to
        determine the job number / URL.

        :param name: queue number, ``int``
        :returns: dictionary of queued information, ``dict``
        '''
        url = self._build_url(Q_ITEM, locals())
        try:
            response = self.jenkins_open(requests.Request('GET', url))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('queue number[%d] does not exist'
                                       % number)
        except (req_exc.HTTPError, NotFoundException):
            raise JenkinsException('queue number[%d] does not exist' % number)
        except ValueError:
            raise JenkinsException(
                'Could not parse JSON info for queue number[%d]' % number
            )

    def get_build_info(self, name, number, depth=0):
        '''Get build information dictionary.

        :param name: Job name, ``str``
        :param number: Build number, ``int``
        :param depth: JSON depth, ``int``
        :returns: dictionary of build information, ``dict``

        Example::

            >>> next_build_number = server.get_job_info('build_name')['nextBuildNumber']
            >>> output = server.build_job('build_name')
            >>> from time import sleep; sleep(10)
            >>> build_info = server.get_build_info('build_name', next_build_number)
            >>> print(build_info)
            {u'building': False, u'changeSet': {u'items': [{u'date': u'2011-12-19T18:01:52.540557Z', u'msg': u'test', u'revision': 66, u'user': u'unknown', u'paths': [{u'editType': u'edit', u'file': u'/branches/demo/index.html'}]}], u'kind': u'svn', u'revisions': [{u'module': u'http://eaas-svn01.i3.level3.com/eaas', u'revision': 66}]}, u'builtOn': u'', u'description': None, u'artifacts': [{u'relativePath': u'dist/eaas-87-2011-12-19_18-01-57.war', u'displayPath': u'eaas-87-2011-12-19_18-01-57.war', u'fileName': u'eaas-87-2011-12-19_18-01-57.war'}, {u'relativePath': u'dist/eaas-87-2011-12-19_18-01-57.war.zip', u'displayPath': u'eaas-87-2011-12-19_18-01-57.war.zip', u'fileName': u'eaas-87-2011-12-19_18-01-57.war.zip'}], u'timestamp': 1324317717000, u'number': 87, u'actions': [{u'parameters': [{u'name': u'SERVICE_NAME', u'value': u'eaas'}, {u'name': u'PROJECT_NAME', u'value': u'demo'}]}, {u'causes': [{u'userName': u'anonymous', u'shortDescription': u'Started by user anonymous'}]}, {}, {}, {}], u'id': u'2011-12-19_18-01-57', u'keepLog': False, u'url': u'http://eaas-jenkins01.i3.level3.com:9080/job/build_war/87/', u'culprits': [{u'absoluteUrl': u'http://eaas-jenkins01.i3.level3.com:9080/user/unknown', u'fullName': u'unknown'}], u'result': u'SUCCESS', u'duration': 8826, u'fullDisplayName': u'build_war #87'}
        '''  # noqa: E501
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(BUILD_INFO, locals())
            ))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('job[%s] number[%d] does not exist'
                                       % (name, number))
        except (req_exc.HTTPError, NotFoundException):
            raise JenkinsException('job[%s] number[%d] does not exist'
                                   % (name, number))
        except ValueError:
            raise JenkinsException(
                'Could not parse JSON info for job[%s] number[%d]'
                % (name, number)
            )

    def get_build_env_vars(self, name, number, depth=0):
        '''Get build environment variables.

        :param name: Job name, ``str``
        :param number: Build number, ``int``
        :param depth: JSON depth, ``int``
        :returns: dictionary of build env vars, ``dict`` or None for workflow jobs,
            or if InjectEnvVars plugin not installed
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(BUILD_ENV_VARS, locals())))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('job[%s] number[%d] does not exist' % (name, number))
        except req_exc.HTTPError:
            raise JenkinsException('job[%s] number[%d] does not exist' % (name, number))
        except ValueError:
            raise JenkinsException(
                'Could not parse JSON info for job[%s] number[%d]' % (name, number))
        except NotFoundException:
            # This can happen on workflow jobs, or if InjectEnvVars plugin not installed
            return None

    def get_build_test_report(self, name, number, depth=0):
        '''Get test results report.

        :param name: Job name, ``str``
        :param number: Build number, ``int``
        :returns: dictionary of test report results, ``dict`` or None if there is no Test Report
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(BUILD_TEST_REPORT, locals())))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('job[%s] number[%d] does not exist' % (name, number))
        except req_exc.HTTPError:
            raise JenkinsException('job[%s] number[%d] does not exist' % (name, number))
        except ValueError:
            raise JenkinsException(
                'Could not parse JSON info for job[%s] number[%d]' % (name, number))
        except NotFoundException:
            # This can happen if the test report wasn't generated for any reason
            return None

    def get_queue_info(self):
        ''':returns: list of job dictionaries, ``[dict]``

        Example::
            >>> queue_info = server.get_queue_info()
            >>> print(queue_info[0])
            {u'task': {u'url': u'http://your_url/job/my_job/', u'color': u'aborted_anime', u'name': u'my_job'}, u'stuck': False, u'actions': [{u'causes': [{u'shortDescription': u'Started by timer'}]}], u'buildable': False, u'params': u'', u'buildableStartMilliseconds': 1315087293316, u'why': u'Build #2,532 is already in progress (ETA:10 min)', u'blocked': True}
        '''  # noqa: E501
        return json.loads(self.jenkins_open(
            requests.Request('GET', self._build_url(Q_INFO))
        ))['items']

    def cancel_queue(self, id):
        '''Cancel a queued build.

        :param id: Jenkins job id number for the build, ``int``
        '''
        # Jenkins seems to always return a 404 when using this REST endpoint
        # https://issues.jenkins-ci.org/browse/JENKINS-21311
        try:
            self.jenkins_open(
                requests.Request(
                    'POST', self._build_url(CANCEL_QUEUE, locals()),
                    headers={'Referer': self.server}))
        except NotFoundException:
            # Exception is expected; cancel_queue() is a best-effort
            # mechanism, so ignore it
            pass

    def get_info(self, item="", query=None):
        """Get information on this Master or item on Master.

        This information includes job list and view information and can be
        used to retreive information on items such as job folders.

        :param item: item to get information about on this Master
        :param query: xpath to extract information about on this Master
        :returns: dictionary of information about Master or item, ``dict``

        Example::

            >>> info = server.get_info()
            >>> jobs = info['jobs']
            >>> print(jobs[0])
            {u'url': u'http://your_url_here/job/my_job/', u'color': u'blue',
            u'name': u'my_job'}

        """
        url = '/'.join((item, INFO)).lstrip('/')
        url = quote(url)
        if query:
            url += query
        try:
            return json.loads(self.jenkins_open(
                requests.Request('GET', self._build_url(url))
            ))
        except (req_exc.HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)
        except ValueError:
            raise JenkinsException("Could not parse JSON info for server[%s]"
                                   % self.server)

    def get_whoami(self, depth=0):
        """Get information about the user account that authenticated to
        Jenkins. This is a simple way to verify that your credentials are
        correct.

        :returns: Information about the current user ``dict``

        Example::

            >>> me = server.get_whoami()
            >>> print me['fullName']
            >>> 'John'

        """
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(WHOAMI_URL, locals())
            ))
            if response is None:
                raise EmptyResponseException(
                    "Error communicating with server[%s]: "
                    "empty response" % self.server)

            return json.loads(response)

        except (req_exc.HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)

    def get_version(self):
        """Get the version of this Master.

        :returns: This master's version number ``str``

        Example::

            >>> info = server.get_version()
            >>> print info
            >>> 1.541

        """
        try:
            request = requests.Request('GET', self._build_url(''))
            request.headers['X-Jenkins'] = '0.0'
            response = self._response_handler(self._request(request))

            return response.headers['X-Jenkins']

        except (req_exc.HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)

    def get_plugins_info(self, depth=2):
        """Get all installed plugins information on this Master.

        This method retrieves information about each plugin that is installed
        on master returning the raw plugin data in a JSON format.

        .. deprecated:: 0.4.9
           Use :func:`get_plugins` instead.

        :param depth: JSON depth, ``int``
        :returns: info on all plugins ``[dict]``

        Example::

            >>> info = server.get_plugins_info()
            >>> print(info)
            [{u'backupVersion': None, u'version': u'0.0.4', u'deleted': False,
            u'supportsDynamicLoad': u'MAYBE', u'hasUpdate': True,
            u'enabled': True, u'pinned': False, u'downgradable': False,
            u'dependencies': [], u'url':
            u'http://wiki.jenkins-ci.org/display/JENKINS/Gearman+Plugin',
            u'longName': u'Gearman Plugin', u'active': True, u'shortName':
            u'gearman-plugin', u'bundled': False}, ..]

        """
        warnings.warn("get_plugins_info() is deprecated, use get_plugins()",
                      DeprecationWarning)
        return [plugin_data for plugin_data in self.get_plugins(depth).values()]

    def get_plugin_info(self, name, depth=2):
        """Get an installed plugin information on this Master.

        This method retrieves information about a specific plugin and returns
        the raw plugin data in a JSON format.
        The passed in plugin name (short or long) must be an exact match.

        .. note:: Calling this method will query Jenkins fresh for the
            information for all plugins on each call. If you need to retrieve
            information for multiple plugins it's recommended to use
            :func:`get_plugins` instead, which will return a multi key
            dictionary that can be accessed via either the short or long name
            of the plugin.

        :param name: Name (short or long) of plugin, ``str``
        :param depth: JSON depth, ``int``
        :returns: a specific plugin ``dict``

        Example::

            >>> info = server.get_plugin_info("Gearman Plugin")
            >>> print(info)
            {u'backupVersion': None, u'version': u'0.0.4', u'deleted': False,
            u'supportsDynamicLoad': u'MAYBE', u'hasUpdate': True,
            u'enabled': True, u'pinned': False, u'downgradable': False,
            u'dependencies': [], u'url':
            u'http://wiki.jenkins-ci.org/display/JENKINS/Gearman+Plugin',
            u'longName': u'Gearman Plugin', u'active': True, u'shortName':
            u'gearman-plugin', u'bundled': False}

        """
        plugins_info = self.get_plugins(depth)
        try:
            return plugins_info[name]
        except KeyError:
            pass

    def get_plugins(self, depth=2):
        """Return plugins info using helper class for version comparison

        This method retrieves information about all the installed plugins and
        uses a Plugin helper class to simplify version comparison. Also uses
        a multi key dict to allow retrieval via either short or long names.

        When printing/dumping the data, the version will transparently return
        a unicode string, which is exactly what was previously returned by the
        API.

        :param depth: JSON depth, ``int``
        :returns: info on all plugins ``[dict]``

        Example::

            >>> j = Jenkins()
            >>> info = j.get_plugins()
            >>> print(info)
            {('gearman-plugin', 'Gearman Plugin'):
              {u'backupVersion': None, u'version': u'0.0.4',
               u'deleted': False, u'supportsDynamicLoad': u'MAYBE',
               u'hasUpdate': True, u'enabled': True, u'pinned': False,
               u'downgradable': False, u'dependencies': [], u'url':
               u'http://wiki.jenkins-ci.org/display/JENKINS/Gearman+Plugin',
               u'longName': u'Gearman Plugin', u'active': True, u'shortName':
               u'gearman-plugin', u'bundled': False}, ...}

        """

        try:
            plugins_info_json = json.loads(self.jenkins_open(
                requests.Request('GET', self._build_url(PLUGIN_INFO, locals()))))
        except (req_exc.HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)
        except ValueError:
            raise JenkinsException("Could not parse JSON info for server[%s]"
                                   % self.server)

        plugins_data = multi_key_dict.multi_key_dict()
        for plugin_data in plugins_info_json['plugins']:
            keys = (str(plugin_data['shortName']), str(plugin_data['longName']))
            plugins_data[keys] = plugins.Plugin(**plugin_data)

        return plugins_data

    def get_jobs(self, folder_depth=0, folder_depth_per_request=10, view_name=None):
        """Get list of jobs.

        Each job is a dictionary with 'name', 'url', 'color' and 'fullname'
        keys.

        If the ``view_name`` parameter is present, the list of
        jobs will be limited to only those configured in the
        specified view. In this case, the job dictionary 'fullname' key
        would be equal to the job name.

        :param folder_depth: Number of levels to search, ``int``. By default
            0, which will limit search to toplevel. None disables the limit.
        :param folder_depth_per_request: Number of levels to fetch at once,
            ``int``. See :func:`get_all_jobs`.
        :param view_name: Name of a Jenkins view for which to
            retrieve jobs, ``str``. By default, the job list is
            not limited to a specific view.
        :returns: list of jobs, ``[{str: str, str: str, str: str, str: str}]``

        Example::

            >>> jobs = server.get_jobs()
            >>> print(jobs)
            [{
                u'name': u'all_tests',
                u'url': u'http://your_url.here/job/all_tests/',
                u'color': u'blue',
                u'fullname': u'all_tests'
            }]

        """

        if view_name:
            return self._get_view_jobs(name=view_name)
        else:
            return self.get_all_jobs(folder_depth=folder_depth,
                                     folder_depth_per_request=folder_depth_per_request)

    def get_all_jobs(self, folder_depth=None, folder_depth_per_request=10):
        """Get list of all jobs recursively to the given folder depth.

        Each job is a dictionary with 'name', 'url', 'color' and 'fullname'
        keys.

        :param folder_depth: Number of levels to search, ``int``. By default
            None, which will search all levels. 0 limits to toplevel.
        :param folder_depth_per_request: Number of levels to fetch at once,
            ``int``. By default 10, which is usually enough to fetch all jobs
            using a single request and still easily fits into an HTTP request.
        :returns: list of jobs, ``[ { str: str} ]``

        .. note::

            On instances with many folders it would not be efficient to fetch
            each folder separately, hence `folder_depth_per_request` levels
            are fetched at once using the ``tree`` query parameter::

                ?tree=jobs[url,color,name,jobs[...,jobs[...,jobs[...,jobs]]]]

            If there are more folder levels than the query asks for, Jenkins
            returns empty [#]_ objects at the deepest level::

                {"name": "folder", "url": "...", "jobs": [{}, {}, ...]}

            This makes it possible to detect when additional requests are
            needed.

            .. [#] Actually recent Jenkins includes a ``_class`` field
                everywhere, but it's missing the requested fields.
        """
        jobs_query = 'jobs'
        for _ in range(folder_depth_per_request):
            jobs_query = JOBS_QUERY_TREE % jobs_query
        jobs_query = JOBS_QUERY % jobs_query

        jobs_list = []
        jobs = [(0, [], self.get_info(query=jobs_query)['jobs'])]
        for lvl, root, lvl_jobs in jobs:
            if not isinstance(lvl_jobs, list):
                lvl_jobs = [lvl_jobs]
            for job in lvl_jobs:
                path = root + [job[u'name']]
                # insert fullname info if it doesn't exist to
                # allow callers to easily reference unambiguously
                if u'fullname' not in job:
                    job[u'fullname'] = '/'.join(path)
                jobs_list.append(job)
                if 'jobs' in job and isinstance(job['jobs'], list):  # folder
                    if folder_depth is None or lvl < folder_depth:
                        children = job['jobs']
                        # once folder_depth_per_request is reached, Jenkins
                        # returns empty objects
                        if any('url' not in child for child in job['jobs']):
                            url_path = ''.join(['/job/' + p for p in path])
                            children = self.get_info(url_path,
                                                     query=jobs_query)['jobs']
                        jobs.append((lvl + 1, path, children))
        return jobs_list

    def copy_job(self, from_name, to_name):
        '''Copy a Jenkins job.

        Will raise an exception whenever the source and destination folder
        for this jobs won't be the same.

        :param from_name: Name of Jenkins job to copy from, ``str``
        :param to_name: Name of Jenkins job to copy to, ``str``
        :throws: :class:`JenkinsException` whenever the source and destination
            folder are not the same
        '''
        from_folder_url, from_short_name = self._get_job_folder(from_name)
        to_folder_url, to_short_name = self._get_job_folder(to_name)
        if from_folder_url != to_folder_url:
            raise JenkinsException('copy[%s to %s] failed, source and destination '
                                   'folder must be the same' % (from_name, to_name))

        self.jenkins_open(requests.Request(
            'POST', self._build_url(COPY_JOB, locals())
        ))
        self.assert_job_exists(to_name, 'create[%s] failed')

    def rename_job(self, from_name, to_name):
        '''Rename an existing Jenkins job

        Will raise an exception whenever the source and destination folder
        for this jobs won't be the same.

        :param from_name: Name of Jenkins job to rename, ``str``
        :param to_name: New Jenkins job name, ``str``
        :throws: :class:`JenkinsException` whenever the source and destination
            folder are not the same
        '''
        from_folder_url, from_short_name = self._get_job_folder(from_name)
        to_folder_url, to_short_name = self._get_job_folder(to_name)
        if from_folder_url != to_folder_url:
            raise JenkinsException('rename[%s to %s] failed, source and destination folder '
                                   'must be the same' % (from_name, to_name))
        self.jenkins_open(requests.Request(
            'POST', self._build_url(RENAME_JOB, locals())
        ))
        self.assert_job_exists(to_name, 'rename[%s] failed')

    def delete_job(self, name):
        '''Delete Jenkins job permanently.

        :param name: Name of Jenkins job, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(DELETE_JOB, locals())
        ))
        if self.job_exists(name):
            raise JenkinsException('delete[%s] failed' % (name))

    def enable_job(self, name):
        '''Enable Jenkins job.

        :param name: Name of Jenkins job, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(ENABLE_JOB, locals())
        ))

    def disable_job(self, name):
        '''Disable Jenkins job.

        To re-enable, call :meth:`Jenkins.enable_job`.

        :param name: Name of Jenkins job, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(DISABLE_JOB, locals())
        ))

    def set_next_build_number(self, name, number):
        '''Set a job's next build number.

        The current next build number is contained within the job
        information retrieved using :meth:`Jenkins.get_job_info`.  If
        the specified next build number is less than the last build
        number, Jenkins will ignore the request.

        Note that the `Next Build Number Plugin
        <https://wiki.jenkins-ci.org/display/JENKINS/Next+Build+Number+Plugin>`_
        must be installed to enable this functionality.

        :param name: Name of Jenkins job, ``str``
        :param number: Next build number to set, ``int``

        Example::

            >>> next_bn = server.get_job_info('job_name')['nextBuildNumber']
            >>> server.set_next_build_number('job_name', next_bn + 50)
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(SET_JOB_BUILD_NUMBER, locals()),
            data=("nextBuildNumber=%d" % number).encode('utf-8')))

    def job_exists(self, name):
        '''Check whether a job exists

        :param name: Name of Jenkins job, ``str``
        :returns: ``True`` if Jenkins job exists
        '''
        folder_url, short_name = self._get_job_folder(name)
        if self.get_job_name(name) == short_name:
            return True

    def jobs_count(self):
        '''Get the number of jobs on the Jenkins server

        :returns: Total number of jobs, ``int``
        '''
        return len(self.get_all_jobs())

    def assert_job_exists(self, name,
                          exception_message='job[%s] does not exist'):
        '''Raise an exception if a job does not exist

        :param name: Name of Jenkins job, ``str``
        :param exception_message: Message to use for the exception. Formatted
                                  with ``name``
        :throws: :class:`JenkinsException` whenever the job does not exist
        '''
        if not self.job_exists(name):
            raise JenkinsException(exception_message % name)

    def create_job(self, name, config_xml):
        '''Create a new Jenkins job

        :param name: Name of Jenkins job, ``str``
        :param config_xml: config file text, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        if self.job_exists(name):
            raise JenkinsException('job[%s] already exists' % (name))

        try:
            self.jenkins_open(requests.Request(
                'POST', self._build_url(CREATE_JOB, locals()),
                data=config_xml.encode('utf-8'),
                headers=DEFAULT_HEADERS
            ))
        except NotFoundException:
            raise JenkinsException('Cannot create job[%s] because folder '
                                   'for the job does not exist' % (name))
        self.assert_job_exists(name, 'create[%s] failed')

    def get_job_config(self, name):
        '''Get configuration of existing Jenkins job.

        :param name: Name of Jenkins job, ``str``
        :returns: job configuration (XML format)
        '''
        folder_url, short_name = self._get_job_folder(name)
        request = requests.Request('GET', self._build_url(CONFIG_JOB, locals()))
        return self.jenkins_open(request)

    def reconfig_job(self, name, config_xml):
        '''Change configuration of existing Jenkins job.

        To create a new job, see :meth:`Jenkins.create_job`.

        :param name: Name of Jenkins job, ``str``
        :param config_xml: New XML configuration, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        reconfig_url = self._build_url(CONFIG_JOB, locals())
        self.jenkins_open(requests.Request(
            'POST', reconfig_url,
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

    def build_job_url(self, name, parameters=None, token=None):
        '''Get URL to trigger build job.

        Authenticated setups may require configuring a token on the server
        side.

        Use ``list of two membered tuples`` to supply parameters with multi
        select options.

        :param name: Name of Jenkins job, ``str``
        :param parameters: parameters for job, or None., ``dict`` or
            ``list of two membered tuples``
        :param token: (optional) token for building job, ``str``
        :returns: URL for building job
        '''
        folder_url, short_name = self._get_job_folder(name)
        if parameters:
            if token:
                if isinstance(parameters, list):
                    parameters.append(('token', token, ))
                elif isinstance(parameters, dict):
                    parameters.update({'token': token})
                else:
                    raise JenkinsException('build parameters can be a dictionary '
                                           'like {"param_key": "param_value", ...} '
                                           'or a list of two membered tuples '
                                           'like [("param_key", "param_value",), ...]')
            return (self._build_url(BUILD_WITH_PARAMS_JOB, locals()) +
                    '?' + urlencode(parameters))
        elif token:
            return (self._build_url(BUILD_JOB, locals()) +
                    '?' + urlencode({'token': token}))
        else:
            return self._build_url(BUILD_JOB, locals())

    def build_job(self, name, parameters=None, token=None):
        '''Trigger build job.

        This method returns a queue item number that you can pass to
        :meth:`Jenkins.get_queue_item`. Note that this queue number is only
        valid for about five minutes after the job completes, so you should
        get/poll the queue information as soon as possible to determine the
        job's URL.

        :param name: name of job
        :param parameters: parameters for job, or ``None``, ``dict``
        :param token: Jenkins API token
        :returns: ``int`` queue item
        '''
        response = self.jenkins_request(requests.Request(
            'POST', self.build_job_url(name, parameters, token)))

        if 'Location' not in response.headers:
            raise EmptyResponseException(
                "Header 'Location' not found in "
                "response from server[%s]" % self.server)

        location = response.headers['Location']
        # location is a queue item, eg. "http://jenkins/queue/item/25/"
        if location.endswith('/'):
            location = location[:-1]
        parts = location.split('/')
        number = int(parts[-1])
        return number

    def run_script(self, script, node=None):
        '''Execute a groovy script on the jenkins master or on a node if
        specified..

        :param script: The groovy script, ``string``
        :param node: Node to run the script on, defaults to None (master).
        :returns: The result of the script run.

        Example::
            >>> info = server.run_script("println(Jenkins.instance.pluginManager.plugins)")
            >>> print(info)
            u'[Plugin:windows-slaves, Plugin:ssh-slaves, Plugin:translation,
            Plugin:cvs, Plugin:nodelabelparameter, Plugin:external-monitor-job,
            Plugin:mailer, Plugin:jquery, Plugin:antisamy-markup-formatter,
            Plugin:maven-plugin, Plugin:pam-auth]'
        '''
        magic_str = ')]}.'
        print_magic_str = 'print("{}")'.format(magic_str)
        data = {'script': "{0}\n{1}".format(script, print_magic_str).encode('utf-8')}
        if node:
            url = self._build_url(NODE_SCRIPT_TEXT, locals())
        else:
            url = self._build_url(SCRIPT_TEXT, locals())

        result = self.jenkins_open(requests.Request(
            'POST', url, data=data))

        if not result.endswith(magic_str):
            raise JenkinsException(result)

        return result[:result.rfind('\n')]

    def install_plugin(self, name, include_dependencies=True):
        '''Install a plugin and its dependencies from the Jenkins public
        repository at http://repo.jenkins-ci.org/repo/org/jenkins-ci/plugins

        :param name: The plugin short name, ``string``
        :param include_dependencies: Install the plugin's dependencies, ``bool``
        :returns: Whether a Jenkins restart is required, ``bool``

        Example::
            >>> info = server.install_plugin("jabber")
            >>> print(info)
            True
        '''
        # using a groovy script because Jenkins does not provide a REST endpoint
        # for installing plugins.
        install = ('Jenkins.instance.updateCenter.getPlugin(\"' + name + '\")'
                   '.deploy();')
        if include_dependencies:
            install = ('Jenkins.instance.updateCenter.getPlugin(\"' + name + '\")'
                       '.getNeededDependencies().each{it.deploy()};') + install

        self.run_script(install)
        # run_script is an async call to run groovy. we need to wait a little
        # before we can get a reliable response on whether a restart is needed
        time.sleep(2)
        is_restart_required = ('Jenkins.instance.updateCenter'
                               '.isRestartRequiredForCompletion()')

        # response is a string (i.e. u'Result: true\n'), return a bool instead
        response_str = self.run_script(is_restart_required)
        response = response_str.split(':')[1].strip().lower() == 'true'
        return response

    def stop_build(self, name, number):
        '''Stop a running Jenkins build.

        :param name: Name of Jenkins job, ``str``
        :param number: Jenkins build number for the job, ``int``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(STOP_BUILD, locals())
        ))

    def delete_build(self, name, number):
        """Delete a Jenkins build.

        :param name: Name of Jenkins job, ``str``
        :param number: Jenkins build number for the job, ``int``
        """
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST',
                          self._build_url(DELETE_BUILD, locals()), b''))

    def wipeout_job_workspace(self, name):
        """Wipe out workspace for given Jenkins job.

        :param name: Name of Jenkins job, ``str``
        """
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request('POST',
                          self._build_url(WIPEOUT_JOB_WORKSPACE,
                                          locals()), b''))

    def get_running_builds(self):
        '''Return list of running builds.

        Each build is a dict with keys 'name', 'number', 'url', 'node',
        and 'executor'.

        :returns: List of builds,
          ``[ { str: str, str: int, str:str, str: str, str: int} ]``

        Example::
            >>> builds = server.get_running_builds()
            >>> print(builds)
            [{'node': 'foo-slave', 'url': 'https://localhost/job/test/15/',
              'executor': 0, 'name': 'test', 'number': 15}]
        '''
        builds = []
        nodes = self.get_nodes()
        for node in nodes:
            # the name returned is not the name to lookup when
            # dealing with master :/
            if node['name'] == 'master':
                node_name = '(master)'
            else:
                node_name = node['name']
            try:
                info = self.get_node_info(node_name, depth=2)
            except JenkinsException as e:
                # Jenkins may 500 on depth >0. If the node info comes back
                # at depth 0 treat it as a node not running any jobs.
                if ('[500]' in str(e) and
                        self.get_node_info(node_name, depth=0)):
                    continue
                else:
                    raise
            for executor in info['executors']:
                executable = executor['currentExecutable']
                if executable and 'PlaceholderTask' not in executable.get('_class', ''):
                    executor_number = executor['number']
                    build_number = executable['number']
                    url = executable['url']
                    m = re.search(r'/job/([^/]+)/.*', urlparse(url).path)
                    job_name = m.group(1)
                    builds.append({'name': job_name,
                                   'number': build_number,
                                   'url': url,
                                   'node': node_name,
                                   'executor': executor_number})
        return builds

    def get_nodes(self, depth=0):
        '''Get a list of nodes connected to the Master

        Each node is a dict with keys 'name' and 'offline'

        :returns: List of nodes, ``[ { str: str, str: bool} ]``
        '''
        try:
            nodes_data = json.loads(self.jenkins_open(
                requests.Request('GET', self._build_url(NODE_LIST, locals()))))
            return [{'name': c["displayName"], 'offline': c["offline"]}
                    for c in nodes_data["computer"]]
        except (req_exc.HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)
        except ValueError:
            raise JenkinsException("Could not parse JSON info for server[%s]"
                                   % self.server)

    def get_node_info(self, name, depth=0):
        '''Get node information dictionary

        :param name: Node name, ``str``
        :param depth: JSON depth, ``int``
        :returns: Dictionary of node info, ``dict``
        '''
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(NODE_INFO, locals())
            ))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('node[%s] does not exist' % name)
        except (req_exc.HTTPError, NotFoundException):
            raise JenkinsException('node[%s] does not exist' % name)
        except ValueError:
            raise JenkinsException("Could not parse JSON info for node[%s]"
                                   % name)

    def node_exists(self, name):
        '''Check whether a node exists

        :param name: Name of Jenkins node, ``str``
        :returns: ``True`` if Jenkins node exists
        '''
        try:
            self.get_node_info(name)
            return True
        except JenkinsException:
            return False

    def assert_node_exists(self, name,
                           exception_message='node[%s] does not exist'):
        '''Raise an exception if a node does not exist

        :param name: Name of Jenkins node, ``str``
        :param exception_message: Message to use for the exception. Formatted
                                  with ``name``
        :throws: :class:`JenkinsException` whenever the node does not exist
        '''
        if not self.node_exists(name):
            raise JenkinsException(exception_message % name)

    def delete_node(self, name):
        '''Delete Jenkins node permanently.

        :param name: Name of Jenkins node, ``str``
        '''
        self.get_node_info(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(DELETE_NODE, locals())
        ))
        if self.node_exists(name):
            raise JenkinsException('delete[%s] failed' % (name))

    def disable_node(self, name, msg=''):
        '''Disable a node

        :param name: Jenkins node name, ``str``
        :param msg: Offline message, ``str``
        '''
        info = self.get_node_info(name)
        if info['offline']:
            return
        self.jenkins_open(requests.Request(
            'POST', self._build_url(TOGGLE_OFFLINE, locals())
        ))

    def enable_node(self, name):
        '''Enable a node

        :param name: Jenkins node name, ``str``
        '''
        info = self.get_node_info(name)
        if not info['offline']:
            return
        msg = ''
        self.jenkins_open(requests.Request(
            'POST', self._build_url(TOGGLE_OFFLINE, locals())
        ))

    def create_node(self, name, numExecutors=2, nodeDescription=None,
                    remoteFS='/var/lib/jenkins', labels=None, exclusive=False,
                    launcher=LAUNCHER_COMMAND, launcher_params={}):
        '''Create a node

        :param name: name of node to create, ``str``
        :param numExecutors: number of executors for node, ``int``
        :param nodeDescription: Description of node, ``str``
        :param remoteFS: Remote filesystem location to use, ``str``
        :param labels: Labels to associate with node, ``str``
        :param exclusive: Use this node for tied jobs only, ``bool``
        :param launcher: The launch method for the slave, ``jenkins.LAUNCHER_COMMAND``, \
        ``jenkins.LAUNCHER_SSH``, ``jenkins.LAUNCHER_JNLP``, ``jenkins.LAUNCHER_WINDOWS_SERVICE``
        :param launcher_params: Additional parameters for the launcher, ``dict``
        '''
        if self.node_exists(name):
            raise JenkinsException('node[%s] already exists' % (name))

        mode = 'NORMAL'
        if exclusive:
            mode = 'EXCLUSIVE'

        launcher_params['stapler-class'] = launcher

        inner_params = {
            'nodeDescription': nodeDescription,
            'numExecutors': numExecutors,
            'remoteFS': remoteFS,
            'labelString': labels,
            'mode': mode,
            'retentionStrategy': {
                'stapler-class':
                'hudson.slaves.RetentionStrategy$Always'
            },
            'nodeProperties': {'stapler-class-bag': 'true'},
            'launcher': launcher_params
        }

        params = {
            'name': name,
            'type': NODE_TYPE,
            'json': json.dumps(inner_params)
        }

        self.jenkins_open(requests.Request(
            'POST', self._build_url(CREATE_NODE, locals()), data=params)
        )

        self.assert_node_exists(name, 'create[%s] failed')

    def get_node_config(self, name):
        '''Get the configuration for a node.

        :param name: Jenkins node name, ``str``
        '''
        get_config_url = self._build_url(CONFIG_NODE, locals())
        return self.jenkins_open(requests.Request('GET', get_config_url))

    def reconfig_node(self, name, config_xml):
        '''Change the configuration for an existing node.

        :param name: Jenkins node name, ``str``
        :param config_xml: New XML configuration, ``str``
        '''
        reconfig_url = self._build_url(CONFIG_NODE, locals())
        self.jenkins_open(requests.Request(
            'POST', reconfig_url,
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

    def get_build_console_output(self, name, number):
        '''Get build console text.

        :param name: Job name, ``str``
        :param number: Build number, ``int``
        :returns: Build console output,  ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(BUILD_CONSOLE_OUTPUT, locals())
            ))
            if response:
                return response
            else:
                raise JenkinsException('job[%s] number[%d] does not exist'
                                       % (name, number))
        except (req_exc.HTTPError, NotFoundException):
            raise JenkinsException('job[%s] number[%d] does not exist'
                                   % (name, number))

    def _get_job_folder(self, name):
        '''Return the name and folder (see cloudbees plugin).

        This is a method to support cloudbees folder plugin.
        Url request should take into account folder path when the job name specify it
        (ex.: 'folder/job')

        :param name: Job name, ``str``
        :returns: Tuple [ 'folder path for Request', 'Name of job without folder path' ]
        '''

        a_path = name.split('/')
        short_name = a_path[-1]
        folder_url = (('job/' + '/job/'.join(a_path[:-1]) + '/')
                      if len(a_path) > 1 else '')

        return folder_url, short_name

    def _get_view_jobs(self, name):
        '''Get list of jobs on the view specified.

        Each job is a dictionary with 'name', 'url', 'color' and 'fullname'
        keys.

        The list of jobs is limited to only those configured in the
        specified view. Each job dictionary 'fullname' key
        is equal to the job name.

        :param view_name: Name of a Jenkins view for which to
            retrieve jobs, ``str``.
        :returns: list of jobs, ``[{str: str, str: str, str: str, str: str}]``
        '''

        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(VIEW_JOBS, locals())
            ))
            if response:
                jobs = json.loads(response)['jobs']
            else:
                raise JenkinsException('view[%s] does not exist' % name)
        except NotFoundException:
            raise JenkinsException('view[%s] does not exist' % name)
        except ValueError:
            raise JenkinsException(
                'Could not parse JSON info for view[%s]' % name)

        for job_dict in jobs:
            job_dict.update({u'fullname': job_dict[u'name']})

        return jobs

    def get_view_name(self, name):
        '''Return the name of a view using the API.

        That is roughly an identity method which can be used to quickly verify
        a view exists or is accessible without causing too much stress on the
        server side.

        :param name: View name, ``str``
        :returns: Name of view or None
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(VIEW_NAME, locals())))
        except NotFoundException:
            return None
        else:
            actual = json.loads(response)['name']
            if actual != short_name:
                raise JenkinsException(
                    'Jenkins returned an unexpected view name %s '
                    '(expected: %s)' % (actual, short_name))
            return name

    def assert_view_exists(self, name,
                           exception_message='view[%s] does not exist'):
        '''Raise an exception if a view does not exist

        :param name: Name of Jenkins view, ``str``
        :param exception_message: Message to use for the exception. Formatted
                                  with ``name``
        :throws: :class:`JenkinsException` whenever the view does not exist
        '''
        if not self.view_exists(name):
            raise NotFoundException(exception_message % name)

    def view_exists(self, name):
        '''Check whether a view exists

        :param name: Name of Jenkins view, ``str``
        :returns: ``True`` if Jenkins view exists
        '''
        if self.get_view_name(name) == name:
            return True

    def get_views(self):
        """Get list of views running.

        Each view is a dictionary with 'name' and 'url' keys.

        :returns: list of views, ``[ { str: str} ]``
        """
        return self.get_info()['views']

    def delete_view(self, name):
        '''Delete Jenkins view permanently.

        :param name: Name of Jenkins view, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(DELETE_VIEW, locals())
        ))
        if self.view_exists(name):
            raise JenkinsException('delete[%s] failed' % (name))

    def create_view(self, name, config_xml):
        '''Create a new Jenkins view

        :param name: Name of Jenkins view, ``str``
        :param config_xml: config file text, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        if self.view_exists(name):
            raise JenkinsException('view[%s] already exists' % (name))

        self.jenkins_open(requests.Request(
            'POST', self._build_url(CREATE_VIEW, locals()),
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))
        self.assert_view_exists(name, 'create[%s] failed')

    def reconfig_view(self, name, config_xml):
        '''Change configuration of existing Jenkins view.

        To create a new view, see :meth:`Jenkins.create_view`.

        :param name: Name of Jenkins view, ``str``
        :param config_xml: New XML configuration, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        reconfig_url = self._build_url(CONFIG_VIEW, locals())
        self.jenkins_open(requests.Request(
            'POST', reconfig_url,
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

    def get_view_config(self, name):
        '''Get configuration of existing Jenkins view.

        :param name: Name of Jenkins view, ``str``
        :returns: view configuration (XML format)
        '''
        folder_url, short_name = self._get_job_folder(name)
        request = requests.Request('GET', self._build_url(CONFIG_VIEW, locals()))
        return self.jenkins_open(request)

    def get_promotion_name(self, name, job_name):
        '''Return the name of a promotion using the API.

        That is roughly an identity method which can be used to
        quickly verify a promotion exists for a job or is accessible
        without causing too much stress on the server side.

        :param name: Promotion name, ``str``
        :param job_name: Job name, ``str``
        :returns: Name of promotion or None
        '''
        folder_url, short_name = self._get_job_folder(job_name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(PROMOTION_NAME, locals())))
        except NotFoundException:
            return None
        else:
            actual = json.loads(response)['name']
            if actual != name:
                raise JenkinsException(
                    'Jenkins returned an unexpected promotion name %s '
                    '(expected: %s)' % (actual, name))
            return actual

    def assert_promotion_exists(self, name, job_name,
                                exception_message='promotion[%s] does not '
                                'exist for job[%s]'):
        '''Raise an exception if a job lacks a promotion

        :param name: Name of Jenkins promotion, ``str``
        :param job_name: Job name, ``str``
        :param exception_message: Message to use for the exception. Formatted
                                  with ``name`` and ``job_name``
        :throws: :class:`JenkinsException` whenever the promotion
            does not exist on a job
        '''
        if not self.promotion_exists(name, job_name):
            raise JenkinsException(exception_message % (name, job_name))

    def promotion_exists(self, name, job_name):
        '''Check whether a job has a certain promotion

        :param name: Name of Jenkins promotion, ``str``
        :param job_name: Job name, ``str``
        :returns: ``True`` if Jenkins promotion exists
        '''
        return self.get_promotion_name(name, job_name) == name

    def get_promotions_info(self, job_name, depth=0):
        '''Get promotion information dictionary of a job

        :param job_name: job_name, ``str``
        :param depth: JSON depth, ``int``
        :returns: Dictionary of promotion info, ``dict``
        '''
        folder_url, short_name = self._get_job_folder(job_name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(PROMOTION_INFO, locals())))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('job[%s] does not exist' % job_name)
        except req_exc.HTTPError:
            raise JenkinsException('job[%s] does not exist' % job_name)
        except ValueError:
            raise JenkinsException("Could not parse JSON info for "
                                   "promotions of job[%s]" % job_name)

    def get_promotions(self, job_name):
        """Get list of promotions running.

        Each promotion is a dictionary with 'name' and 'url' keys.

        :param job_name: Job name, ``str``
        :returns: list of promotions, ``[ { str: str} ]``
        """
        return self.get_promotions_info(job_name)['processes']

    def delete_promotion(self, name, job_name):
        '''Delete Jenkins promotion permanently.

        :param name: Name of Jenkins promotion, ``str``
        :param job_name: Job name, ``str``
        '''
        folder_url, short_name = self._get_job_folder(job_name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(DELETE_PROMOTION, locals())
        ))
        if self.promotion_exists(name, job_name):
            raise JenkinsException('delete[%s] from job[%s] failed' %
                                   (name, job_name))

    def create_promotion(self, name, job_name, config_xml):
        '''Create a new Jenkins promotion

        :param name: Name of Jenkins promotion, ``str``
        :param job_name: Job name, ``str``
        :param config_xml: config file text, ``str``
        '''
        if self.promotion_exists(name, job_name):
            raise JenkinsException('promotion[%s] already exists at job[%s]'
                                   % (name, job_name))

        folder_url, short_name = self._get_job_folder(job_name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(CREATE_PROMOTION, locals()),
            data=config_xml.encode('utf-8'), headers=DEFAULT_HEADERS))
        self.assert_promotion_exists(name, job_name, 'create[%s] at '
                                     'job[%s] failed')

    def reconfig_promotion(self, name, job_name, config_xml):
        '''Change configuration of existing Jenkins promotion.

        To create a new promotion, see :meth:`Jenkins.create_promotion`.

        :param name: Name of Jenkins promotion, ``str``
        :param job_name: Job name, ``str``
        :param config_xml: New XML configuration, ``str``
        '''
        folder_url, short_name = self._get_job_folder(job_name)
        reconfig_url = self._build_url(CONFIG_PROMOTION, locals())
        self.jenkins_open(requests.Request(
            'POST', reconfig_url,
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))

    def get_promotion_config(self, name, job_name):
        '''Get configuration of existing Jenkins promotion.

        :param name: Name of Jenkins promotion, ``str``
        :param job_name: Job name, ``str``
        :returns: promotion configuration (XML format)
        '''
        folder_url, short_name = self._get_job_folder(job_name)
        request = requests.Request(
            'GET', self._build_url(CONFIG_PROMOTION, locals()))
        return self.jenkins_open(request)

    def _get_tag_text(self, name, xml):
        '''Get text of tag from xml

        :param name: XML tag name, ``str``
        :param xml: XML configuration, ``str``
        :returns: Text of tag, ``str``
        :throws: :class:`JenkinsException` whenever tag does not exist
            or has invalidated text
        '''
        tag = ET.fromstring(xml).find(name)
        try:
            text = tag.text.strip()
            if text:
                return text
            raise JenkinsException("tag[%s] is invalidated" % name)
        except AttributeError:
            raise JenkinsException("tag[%s] is invalidated" % name)

    def assert_folder(self, name, exception_message='job[%s] is not a folder'):
        '''Raise an exception if job is not Cloudbees Folder

        :param name: Name of job, ``str``
        :param exception_message: Message to use for the exception.
        :throws: :class:`JenkinsException` whenever the job is
            not Cloudbees Folder
        '''
        if not self.is_folder(name):
            raise JenkinsException(exception_message % name)

    def is_folder(self, name):
        '''Check whether a job is Cloudbees Folder

        :param name: Job name, ``str``
        :returns: ``True`` if job is folder, ``False`` otherwise
        '''
        return 'com.cloudbees.hudson.plugins.folder.Folder' \
            == self.get_job_info(name)['_class']

    def assert_credential_exists(self, name, folder_name, domain_name='_',
                                 exception_message='credential[%s] does not '
                                 'exist in the domain[%s] of [%s]'):
        '''Raise an exception if credential does not exist in domain of folder

        :param name: Name of credential, ``str``
        :param folder_name: Folder name, ``str``
        :param domain_name: Domain name, default is '_', ``str``
        :param exception_message: Message to use for the exception.
                                  Formatted with ``name``, ``domain_name``,
                                  and ``folder_name``
        :throws: :class:`JenkinsException` whenever the credentail
            does not exist in domain of folder
        '''
        if not self.credential_exists(name, folder_name, domain_name):
            raise JenkinsException(exception_message
                                   % (name, domain_name, folder_name))

    def credential_exists(self, name, folder_name, domain_name='_'):
        '''Check whether a credentail exists in domain of folder

        :param name: Name of credentail, ``str``
        :param folder_name: Folder name, ``str``
        :param domain_name: Domain name, default is '_', ``str``
        :returns: ``True`` if credentail exists, ``False`` otherwise
        '''
        try:
            return self.get_credential_info(name, folder_name,
                                            domain_name)['id'] == name
        except JenkinsException:
            return False

    def get_credential_info(self, name, folder_name, domain_name='_'):
        '''Get credential information dictionary in domain of folder

        :param name: Name of credentail, ``str``
        :param folder_name: folder_name, ``str``
        :param domain_name: Domain name, default is '_', ``str``
        :returns: Dictionary of credential info, ``dict``
        '''
        self.assert_folder(folder_name)
        folder_url, short_name = self._get_job_folder(folder_name)
        try:
            response = self.jenkins_open(requests.Request(
                'GET', self._build_url(CREDENTIAL_INFO, locals())
            ))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('credential[%s] does not exist '
                                       'in the domain[%s] of [%s]'
                                       % (name, domain_name, folder_name))
        except (req_exc.HTTPError, NotFoundException):
            raise JenkinsException('credential[%s] does not exist '
                                   'in the domain[%s] of [%s]'
                                   % (name, domain_name, folder_name))
        except ValueError:
            raise JenkinsException(
                'Could not parse JSON info for credential[%s] '
                'in the domain[%s] of [%s]'
                % (name, domain_name, folder_name)
            )

    def get_credential_config(self, name, folder_name, domain_name='_'):
        '''Get configuration of credential in domain of folder.

        :param name: Name of credentail, ``str``
        :param folder_name: Folder name, ``str``
        :param domain_name: Domain name, default is '_', ``str``
        :returns: Credential configuration (XML format)
        '''
        self.assert_folder(folder_name)
        folder_url, short_name = self._get_job_folder(folder_name)
        return self.jenkins_open(requests.Request(
            'GET', self._build_url(CONFIG_CREDENTIAL, locals())
            ))

    def create_credential(self, folder_name, config_xml,
                          domain_name='_'):
        '''Create credentail in domain of folder

        :param folder_name: Folder name, ``str``
        :param config_xml: New XML configuration, ``str``
        :param domain_name: Domain name, default is '_', ``str``
        '''
        folder_url, short_name = self._get_job_folder(folder_name)
        name = self._get_tag_text('id', config_xml)
        if self.credential_exists(name, folder_name, domain_name):
            raise JenkinsException('credential[%s] already exists '
                                   'in the domain[%s] of [%s]'
                                   % (name, domain_name, folder_name))

        self.jenkins_open(requests.Request(
            'POST', self._build_url(CREATE_CREDENTIAL, locals()),
            data=config_xml.encode('utf-8'),
            headers=DEFAULT_HEADERS
        ))
        self.assert_credential_exists(name, folder_name, domain_name,
                                      'create[%s] failed in the '
                                      'domain[%s] of [%s]')

    def delete_credential(self, name, folder_name, domain_name='_'):
        '''Delete credential from domain of folder

        :param name: Name of credentail, ``str``
        :param folder_name: Folder name, ``str``
        :param domain_name: Domain name, default is '_', ``str``
        '''
        folder_url, short_name = self._get_job_folder(folder_name)
        self.jenkins_open(requests.Request(
            'DELETE', self._build_url(CONFIG_CREDENTIAL, locals())
            ))
        if self.credential_exists(name, folder_name, domain_name):
            raise JenkinsException('delete credential[%s] from '
                                   'domain[%s] of [%s] failed'
                                   % (name, domain_name, folder_name))

    def reconfig_credential(self, folder_name, config_xml, domain_name='_'):
        '''Reconfig credential with new config in domain of folder

        :param folder_name: Folder name, ``str``
        :param config_xml: New XML configuration, ``str``
        :param domain_name: Domain name, default is '_', ``str``
        '''
        folder_url, short_name = self._get_job_folder(folder_name)
        name = self._get_tag_text('id', config_xml)
        self.assert_credential_exists(name, folder_name, domain_name)
        self.jenkins_open(requests.Request(
            'POST', self._build_url(CONFIG_CREDENTIAL, locals())
            ))

    def list_credentials(self, folder_name, domain_name='_'):
        '''List credentials in domain of folder

        :param folder_name: Folder name, ``str``
        :param domain_name: Domain name, default is '_', ``str``
        :returns: Credentials list, ``list``
        '''
        self.assert_folder(folder_name)
        folder_url, short_name = self._get_job_folder(folder_name)
        response = self.jenkins_open(requests.Request(
            'GET', self._build_url(LIST_CREDENTIALS, locals())
        ))
        return json.loads(response)['credentials']

    def quiet_down(self):
        '''Prepare Jenkins for shutdown.

        No new builds will be started allowing running builds to complete
        prior to shutdown of the server.
        '''
        request = requests.Request('POST', self._build_url(QUIET_DOWN))
        self.jenkins_open(request)
        info = self.get_info()
        if not info['quietingDown']:
            raise JenkinsException('quiet down failed')

    def wait_for_normal_op(self, timeout):
        '''Wait for jenkins to enter normal operation mode.

        :param timeout: number of seconds to wait, ``int``
            Note this is not the same as the connection timeout set via
            __init__ as that controls the socket timeout. Instead this is
            how long to wait until the status returned.
        :returns: ``True`` if Jenkins became ready in time, ``False``
                   otherwise.

        Setting timeout to be less than the configured connection timeout
        may result in this waiting for at least the connection timeout
        length of time before returning. It is recommended that the timeout
        here should be at least as long as any set connection timeout.
        '''
        if timeout < 0:
            raise ValueError("Timeout must be >= 0 not %d" % timeout)

        if (not self._timeout_warning_issued and
                self.timeout != socket._GLOBAL_DEFAULT_TIMEOUT and
                timeout < self.timeout):
            warnings.warn("Requested timeout to wait for jenkins to resume "
                          "normal operations is less than configured "
                          "connection timeout. Unexpected behaviour may "
                          "occur.")
            self._timeout_warning_issued = True

        start_time = time.time()

        def is_ready():
            # only call get_version until it returns without exception
            while True:
                if self.get_version():
                    while True:
                        # json API will only return valid info once Jenkins
                        # is ready, so just check any known field exists
                        # when not in normal mode, most requests will
                        # be ignored or fail
                        yield 'mode' in self.get_info()
                else:
                    yield False

        while True:
            try:
                if next(is_ready()):
                    return True
            except (KeyError, JenkinsException):
                # key missing from JSON, empty response or errors in
                # get_info due to incomplete HTTP responses
                pass
            # check time passed as the communication will also
            # take time
            if time.time() > start_time + timeout:
                break
            time.sleep(1)

        return False
