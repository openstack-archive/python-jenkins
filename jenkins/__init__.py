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

See examples at :doc:`examples`
'''

import base64
import json
import re
import socket
import sys
import warnings

import six
from six.moves.http_client import BadStatusLine
from six.moves.urllib.error import HTTPError
from six.moves.urllib.error import URLError
from six.moves.urllib.parse import quote, urlencode
from six.moves.urllib.request import Request, urlopen

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
JOBS_QUERY = '?tree=jobs[url,color,name,jobs]'
JOB_INFO = '%(folder_url)sjob/%(short_name)s/api/json?depth=%(depth)s'
JOB_NAME = '%(folder_url)sjob/%(short_name)s/api/json?tree=name'
Q_INFO = 'queue/api/json?depth=0'
CANCEL_QUEUE = 'queue/cancelItem?id=%(id)s'
CREATE_JOB = '%(folder_url)screateItem?name=%(short_name)s'  # also post config.xml
CONFIG_JOB = '%(folder_url)sjob/%(short_name)s/config.xml'
DELETE_JOB = '%(folder_url)sjob/%(short_name)s/doDelete'
ENABLE_JOB = '%(folder_url)sjob/%(short_name)s/enable'
DISABLE_JOB = '%(folder_url)sjob/%(short_name)s/disable'
COPY_JOB = '%(from_folder_url)screateItem?name=%(to_short_name)s&mode=copy&from=%(from_short_name)s'
RENAME_JOB = '%(from_folder_url)sjob/%(from_short_name)s/doRename?newName=%(to_short_name)s'
BUILD_JOB = '%(folder_url)sjob/%(short_name)s/build'
STOP_BUILD = '%(folder_url)sjob/%(short_name)s/%(number)s/stop'
BUILD_WITH_PARAMS_JOB = '%(folder_url)sjob/%(short_name)s/buildWithParameters'
BUILD_INFO = '%(folder_url)sjob/%(short_name)s/%(number)d/api/json?depth=%(depth)s'
BUILD_CONSOLE_OUTPUT = '%(folder_url)sjob/%(short_name)s/%(number)d/consoleText'
NODE_LIST = 'computer/api/json'
CREATE_NODE = 'computer/doCreateItem?%s'
DELETE_NODE = 'computer/%(name)s/doDelete'
NODE_INFO = 'computer/%(name)s/api/json?depth=%(depth)s'
NODE_TYPE = 'hudson.slaves.DumbSlave$DescriptorImpl'
TOGGLE_OFFLINE = 'computer/%(name)s/toggleOffline?offlineMessage=%(msg)s'
CONFIG_NODE = 'computer/%(name)s/config.xml'
VIEW_NAME = 'view/%(name)s/api/json?tree=name'
CREATE_VIEW = 'createView?name=%(name)s'
CONFIG_VIEW = 'view/%(name)s/config.xml'
DELETE_VIEW = 'view/%(name)s/doDelete'
SCRIPT_TEXT = 'scriptText'

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


def auth_headers(username, password):
    '''Simple implementation of HTTP Basic Authentication.

    Returns the 'Authentication' header value.
    '''
    auth = '%s:%s' % (username, password)
    if isinstance(auth, six.text_type):
        auth = auth.encode('utf-8')
    return b'Basic ' + base64.b64encode(auth)


class Jenkins(object):

    def __init__(self, url, username=None, password=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT):
        '''Create handle to Jenkins instance.

        All methods will raise :class:`JenkinsException` on failure.

        :param username: Server username, ``str``
        :param password: Server password, ``str``
        :param url: URL of Jenkins server, ``str``
        :param timeout: Server connection timeout in secs (default: not set), ``int``
        '''
        if url[-1] == '/':
            self.server = url
        else:
            self.server = url + '/'
        if username is not None and password is not None:
            self.auth = auth_headers(username, password)
        else:
            self.auth = None
        self.crumb = None
        self.timeout = timeout

    def _get_encoded_params(self, params):
        for k, v in params.items():
            if k in ["name", "msg", "short_name", "from_short_name",
                     "to_short_name", "folder_url", "from_folder_url", "to_folder_url"]:
                params[k] = quote(v)
        return params

    def maybe_add_crumb(self, req):
        # We don't know yet whether we need a crumb
        if self.crumb is None:
            try:
                response = self.jenkins_open(Request(
                    self.server + CRUMB_URL), add_crumb=False)
            except (NotFoundException, EmptyResponseException):
                self.crumb = False
            else:
                self.crumb = json.loads(response)
        if self.crumb:
            req.add_header(self.crumb['crumbRequestField'], self.crumb['crumb'])

    def get_job_info(self, name, depth=0):
        '''Get job information dictionary.

        :param name: Job name, ``str``
        :param depth: JSON depth, ``int``
        :returns: dictionary of job information
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(Request(
                self.server + JOB_INFO % self._get_encoded_params(locals())))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('job[%s] does not exist' % name)
        except HTTPError:
            raise JenkinsException('job[%s] does not exist' % name)
        except ValueError:
            raise JenkinsException(
                "Could not parse JSON info for job[%s]" % name)

    def get_job_info_regex(self, pattern, depth=0):
        '''Get a list of jobs information that contain names which match the
           regex pattern.

        :param pattern: regex pattern, ``str``
        :param depth: JSON depth, ``int``
        :returns: List of jobs info, ``list``
        '''
        result = []
        jobs = self.get_jobs()
        for job in jobs:
            if re.search(pattern, job['name']):
                result.append(self.get_job_info(job['name'], depth=depth))

        return result

    def get_job_name(self, name):
        '''Return the name of a job using the API.

        That is roughly an identity method which can be used to quickly verify
        a job exist or is accessible without causing too much stress on the
        server side.

        :param name: Job name, ``str``
        :returns: Name of job or None
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(
                Request(self.server + JOB_NAME %
                        self._get_encoded_params(locals())))
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

    def jenkins_open(self, req, add_crumb=True):
        '''Utility routine for opening an HTTP request to a Jenkins server.

        This should only be used to extends the :class:`Jenkins` API.
        '''
        try:
            if self.auth:
                req.add_header('Authorization', self.auth)
            if add_crumb:
                self.maybe_add_crumb(req)
            response = urlopen(req, timeout=self.timeout).read()
            if response is None:
                raise EmptyResponseException(
                    "Error communicating with server[%s]: "
                    "empty response" % self.server)
            return response.decode('utf-8')
        except HTTPError as e:
            # Jenkins's funky authentication means its nigh impossible to
            # distinguish errors.
            if e.code in [401, 403, 500]:
                # six.moves.urllib.error.HTTPError provides a 'reason'
                # attribute for all python version except for ver 2.6
                # Falling back to HTTPError.msg since it contains the
                # same info as reason
                raise JenkinsException(
                    'Error in request. ' +
                    'Possibly authentication failed [%s]: %s' % (
                        e.code, e.msg)
                )
            elif e.code == 404:
                raise NotFoundException('Requested item could not be found')
            else:
                raise
        except socket.timeout as e:
            raise TimeoutException('Error in request: %s' % (e))
        except URLError as e:
            # python 2.6 compatibility to ensure same exception raised
            # since URLError wraps a socket timeout on python 2.6.
            if str(e.reason) == "timed out":
                raise TimeoutException('Error in request: %s' % (e.reason))
            raise JenkinsException('Error in request: %s' % (e.reason))

    def get_build_info(self, name, number, depth=0):
        '''Get build information dictionary.

        :param name: Job name, ``str``
        :param name: Build number, ``int``
        :param depth: JSON depth, ``int``
        :returns: dictionary of build information, ``dict``

        Example::

            >>> next_build_number = server.get_job_info('build_name')['nextBuildNumber']
            >>> output = server.build_job('build_name')
            >>> from time import sleep; sleep(10)
            >>> build_info = server.get_build_info('build_name', next_build_number)
            >>> print(build_info)
            {u'building': False, u'changeSet': {u'items': [{u'date': u'2011-12-19T18:01:52.540557Z', u'msg': u'test', u'revision': 66, u'user': u'unknown', u'paths': [{u'editType': u'edit', u'file': u'/branches/demo/index.html'}]}], u'kind': u'svn', u'revisions': [{u'module': u'http://eaas-svn01.i3.level3.com/eaas', u'revision': 66}]}, u'builtOn': u'', u'description': None, u'artifacts': [{u'relativePath': u'dist/eaas-87-2011-12-19_18-01-57.war', u'displayPath': u'eaas-87-2011-12-19_18-01-57.war', u'fileName': u'eaas-87-2011-12-19_18-01-57.war'}, {u'relativePath': u'dist/eaas-87-2011-12-19_18-01-57.war.zip', u'displayPath': u'eaas-87-2011-12-19_18-01-57.war.zip', u'fileName': u'eaas-87-2011-12-19_18-01-57.war.zip'}], u'timestamp': 1324317717000, u'number': 87, u'actions': [{u'parameters': [{u'name': u'SERVICE_NAME', u'value': u'eaas'}, {u'name': u'PROJECT_NAME', u'value': u'demo'}]}, {u'causes': [{u'userName': u'anonymous', u'shortDescription': u'Started by user anonymous'}]}, {}, {}, {}], u'id': u'2011-12-19_18-01-57', u'keepLog': False, u'url': u'http://eaas-jenkins01.i3.level3.com:9080/job/build_war/87/', u'culprits': [{u'absoluteUrl': u'http://eaas-jenkins01.i3.level3.com:9080/user/unknown', u'fullName': u'unknown'}], u'result': u'SUCCESS', u'duration': 8826, u'fullDisplayName': u'build_war #87'}
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(Request(
                self.server + BUILD_INFO % self._get_encoded_params(locals())))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('job[%s] number[%d] does not exist'
                                       % (name, number))
        except HTTPError:
            raise JenkinsException('job[%s] number[%d] does not exist'
                                   % (name, number))
        except ValueError:
            raise JenkinsException(
                'Could not parse JSON info for job[%s] number[%d]'
                % (name, number)
            )

    def get_queue_info(self):
        ''':returns: list of job dictionaries, ``[dict]``

        Example::
            >>> queue_info = server.get_queue_info()
            >>> print(queue_info[0])
            {u'task': {u'url': u'http://your_url/job/my_job/', u'color': u'aborted_anime', u'name': u'my_job'}, u'stuck': False, u'actions': [{u'causes': [{u'shortDescription': u'Started by timer'}]}], u'buildable': False, u'params': u'', u'buildableStartMilliseconds': 1315087293316, u'why': u'Build #2,532 is already in progress (ETA:10 min)', u'blocked': True}
        '''
        return json.loads(self.jenkins_open(
            Request(self.server + Q_INFO)
        ))['items']

    def cancel_queue(self, id):
        '''Cancel a queued build.

        :param id: Jenkins job id number for the build, ``int``
        '''
        # Jenkins seems to always return a 404 when using this REST endpoint
        # https://issues.jenkins-ci.org/browse/JENKINS-21311
        try:
            self.jenkins_open(
                Request(self.server + CANCEL_QUEUE % locals(), b'',
                        headers={'Referer': self.server}))
        except NotFoundException:
            # Exception is expected; cancel_queue() is a best-effort
            # mechanism, so ignore it
            pass

    def get_info(self, item=None, query=None):
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
        if item:
            url = "%s%s/%s" % (self.server, item, INFO)
        else:
            url = "%s%s" % (self.server, INFO)
        if query:
            url += query
        try:
            return json.loads(self.jenkins_open(Request(url)))
        except (HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)
        except ValueError:
            raise JenkinsException("Could not parse JSON info for server[%s]"
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
            request = Request(self.server)
            request.add_header('X-Jenkins', '0.0')
            response = urlopen(request, timeout=self.timeout)
            if response is None:
                raise EmptyResponseException(
                    "Error communicating with server[%s]: "
                    "empty response" % self.server)

            if six.PY2:
                return response.info().getheader('X-Jenkins')

            if six.PY3:
                return response.getheader('X-Jenkins')

        except (HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)

    def get_plugins_info(self, depth=2):
        """Get all installed plugins information on this Master.

        This method retrieves information about each plugin that is installed
        on master.

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
        try:
            plugins_info = json.loads(self.jenkins_open(
                Request(self.server + PLUGIN_INFO % locals())))
            return plugins_info['plugins']
        except (HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)
        except ValueError:
            raise JenkinsException("Could not parse JSON info for server[%s]"
                                   % self.server)

    def get_plugin_info(self, name, depth=2):
        """Get an installed plugin information on this Master.

        This method retrieves information about a speicifc plugin.
        The passed in plugin name (short or long) must be an exact match.

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
        try:
            plugins_info = json.loads(self.jenkins_open(
                Request(self.server + PLUGIN_INFO % self._get_encoded_params(locals()))))
            for plugin in plugins_info['plugins']:
                if plugin['longName'] == name or plugin['shortName'] == name:
                    return plugin
        except (HTTPError, BadStatusLine):
            raise BadHTTPException("Error communicating with server[%s]"
                                   % self.server)
        except ValueError:
            raise JenkinsException("Could not parse JSON info for server[%s]"
                                   % self.server)

    def get_jobs(self, folder_depth=None):
        """Get list of jobs running.

        Each job is a dictionary with 'name', 'url', and 'color' keys.

        :param folder_depth: Number of levels to search, ``int``
        :returns: list of jobs, ``[ { str: str} ]``
        """
        jobs_list = []

        jobs = [(0, None, self.get_info(query=JOBS_QUERY)['jobs'])]
        for lvl, root, lvl_jobs in jobs:
            if not isinstance(lvl_jobs, list):
                lvl_jobs = [lvl_jobs]
            for job in lvl_jobs:
                if 'jobs' in job:  # folder
                    if not folder_depth or lvl < folder_depth:
                        if root:
                            path = '%s/job/%s/' % (root, job['name'])
                        else:
                            path = 'job/%s/' % job['name']
                        jobs.append(
                            (lvl + 1, path,
                             self.get_info(path,
                                           query=JOBS_QUERY)['jobs']))
                else:
                    # insert fullname info if it doesn't exist to
                    # allow callers to easily reference unambiguously
                    if root and 'fullname' not in job:
                        fullname = [p for p in root.split('/')
                                    if p and p != 'job']
                        fullname.append(job['name'])
                        job['fullname'] = '/'.join(fullname)
                    jobs_list.append(job)
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

        self.jenkins_open(Request(
            self.server + COPY_JOB % self._get_encoded_params(locals()),
            b''))
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
        self.jenkins_open(Request(
            self.server + RENAME_JOB % self._get_encoded_params(locals()),
            b''))
        self.assert_job_exists(to_name, 'rename[%s] failed')

    def delete_job(self, name):
        '''Delete Jenkins job permanently.

        :param name: Name of Jenkins job, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(Request(
            self.server + DELETE_JOB % self._get_encoded_params(locals()),
            b''))
        if self.job_exists(name):
            raise JenkinsException('delete[%s] failed' % (name))

    def enable_job(self, name):
        '''Enable Jenkins job.

        :param name: Name of Jenkins job, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(Request(
            self.server + ENABLE_JOB % self._get_encoded_params(locals()),
            b''))

    def disable_job(self, name):
        '''Disable Jenkins job.

        To re-enable, call :meth:`Jenkins.enable_job`.

        :param name: Name of Jenkins job, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(Request(
            self.server + DISABLE_JOB % self._get_encoded_params(locals()),
            b''))

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
        return len(self.get_jobs())

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
            self.jenkins_open(Request(
                self.server + CREATE_JOB % self._get_encoded_params(locals()),
                config_xml.encode('utf-8'), DEFAULT_HEADERS))
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
        request = Request(self.server + CONFIG_JOB % self._get_encoded_params(locals()))
        return self.jenkins_open(request)

    def reconfig_job(self, name, config_xml):
        '''Change configuration of existing Jenkins job.

        To create a new job, see :meth:`Jenkins.create_job`.

        :param name: Name of Jenkins job, ``str``
        :param config_xml: New XML configuration, ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        reconfig_url = self.server + CONFIG_JOB % self._get_encoded_params(locals())
        self.jenkins_open(Request(reconfig_url, config_xml.encode('utf-8'),
                                  DEFAULT_HEADERS))

    def build_job_url(self, name, parameters=None, token=None):
        '''Get URL to trigger build job.

        Authenticated setups may require configuring a token on the server
        side.

        :param parameters: parameters for job, or None., ``dict``
        :param token: (optional) token for building job, ``str``
        :returns: URL for building job
        '''
        folder_url, short_name = self._get_job_folder(name)
        if parameters:
            if token:
                parameters['token'] = token
            return (self.server + BUILD_WITH_PARAMS_JOB % self._get_encoded_params(locals()) +
                    '?' + urlencode(parameters))
        elif token:
            return (self.server + BUILD_JOB % self._get_encoded_params(locals()) +
                    '?' + urlencode({'token': token}))
        else:
            return self.server + BUILD_JOB % self._get_encoded_params(locals())

    def build_job(self, name, parameters=None, token=None):
        '''Trigger build job.

        :param name: name of job
        :param parameters: parameters for job, or ``None``, ``dict``
        :param token: Jenkins API token
        '''
        return self.jenkins_open(Request(
            self.build_job_url(name, parameters, token), b''))

    def run_script(self, script):
        '''Execute a groovy script on the jenkins master.

        :param script: The groovy script, ``string``
        :returns: The result of the script run.

        Example::
            >>> info = server.run_script("println(Jenkins.instance.pluginManager.plugins)")
            >>> print(info)
            u'[Plugin:windows-slaves, Plugin:ssh-slaves, Plugin:translation,
            Plugin:cvs, Plugin:nodelabelparameter, Plugin:external-monitor-job,
            Plugin:mailer, Plugin:jquery, Plugin:antisamy-markup-formatter,
            Plugin:maven-plugin, Plugin:pam-auth]'
        '''
        return self.jenkins_open(Request(self.server + SCRIPT_TEXT,
                                         "script=".encode('utf-8') + script.encode('utf-8')))

    def stop_build(self, name, number):
        '''Stop a running Jenkins build.

        :param name: Name of Jenkins job, ``str``
        :param number: Jenkins build number for the job, ``int``
        '''
        folder_url, short_name = self._get_job_folder(name)
        self.jenkins_open(Request(
            self.server + STOP_BUILD % self._get_encoded_params(locals()),
            b''))

    def get_nodes(self):
        '''Get a list of nodes connected to the Master

        Each node is a dict with keys 'name' and 'offline'

        :returns: List of nodes, ``[ { str: str, str: bool} ]``
        '''
        try:
            nodes_data = json.loads(self.jenkins_open(Request(self.server + NODE_LIST)))
            return [{'name': c["displayName"], 'offline': c["offline"]}
                    for c in nodes_data["computer"]]
        except (HTTPError, BadStatusLine):
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
            response = self.jenkins_open(Request(
                self.server + NODE_INFO % self._get_encoded_params(locals())))
            if response:
                return json.loads(response)
            else:
                raise JenkinsException('node[%s] does not exist' % name)
        except HTTPError:
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
        self.jenkins_open(Request(
            self.server + DELETE_NODE % self._get_encoded_params(locals()),
            b''))
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
        self.jenkins_open(Request(
            self.server + TOGGLE_OFFLINE % self._get_encoded_params(locals()),
            b''))

    def enable_node(self, name):
        '''Enable a node

        :param name: Jenkins node name, ``str``
        '''
        info = self.get_node_info(name)
        if not info['offline']:
            return
        msg = ''
        self.jenkins_open(Request(
            self.server + TOGGLE_OFFLINE % self._get_encoded_params(locals()),
            b''))

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
        :param launcher: The launch method for the slave, ``jenkins.LAUNCHER_COMMAND``, ``jenkins.LAUNCHER_SSH``, ``jenkins.LAUNCHER_JNLP``, ``jenkins.LAUNCHER_WINDOWS_SERVICE``
        :param launcher_params: Additional parameters for the launcher, ``dict``
        '''
        if self.node_exists(name):
            raise JenkinsException('node[%s] already exists' % (name))

        mode = 'NORMAL'
        if exclusive:
            mode = 'EXCLUSIVE'

        launcher_params['stapler-class'] = launcher

        inner_params = {
            'name': name,
            'nodeDescription': nodeDescription,
            'numExecutors': numExecutors,
            'remoteFS': remoteFS,
            'labelString': labels,
            'mode': mode,
            'type': NODE_TYPE,
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

        self.jenkins_open(Request(
            self.server + CREATE_NODE % urlencode(params), b''))

        self.assert_node_exists(name, 'create[%s] failed')

    def get_node_config(self, name):
        '''Get the configuration for a node.

        :param name: Jenkins node name, ``str``
        '''
        get_config_url = self.server + CONFIG_NODE % self._get_encoded_params(locals())
        return self.jenkins_open(Request(get_config_url))

    def reconfig_node(self, name, config_xml):
        '''Change the configuration for an existing node.

        :param name: Jenkins node name, ``str``
        :param config_xml: New XML configuration, ``str``
        '''
        reconfig_url = self.server + CONFIG_NODE % self._get_encoded_params(locals())
        self.jenkins_open(Request(reconfig_url, config_xml.encode('utf-8'), DEFAULT_HEADERS))

    def get_build_console_output(self, name, number):
        '''Get build console text.

        :param name: Job name, ``str``
        :param name: Build number, ``int``
        :returns: Build console output,  ``str``
        '''
        folder_url, short_name = self._get_job_folder(name)
        try:
            response = self.jenkins_open(Request(
                self.server + BUILD_CONSOLE_OUTPUT % self._get_encoded_params(locals())))
            if response:
                return response
            else:
                raise JenkinsException('job[%s] number[%d] does not exist'
                                       % (name, number))
        except HTTPError:
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

    def get_view_name(self, name):
        '''Return the name of a view using the API.

        That is roughly an identity method which can be used to quickly verify
        a view exists or is accessible without causing too much stress on the
        server side.

        :param name: View name, ``str``
        :returns: Name of view or None
        '''
        try:
            response = self.jenkins_open(
                Request(self.server + VIEW_NAME %
                        self._get_encoded_params(locals())))
        except NotFoundException:
            return None
        else:
            actual = json.loads(response)['name']
            if actual != name:
                raise JenkinsException(
                    'Jenkins returned an unexpected view name %s '
                    '(expected: %s)' % (actual, name))
            return actual

    def assert_view_exists(self, name,
                           exception_message='view[%s] does not exist'):
        '''Raise an exception if a view does not exist

        :param name: Name of Jenkins view, ``str``
        :param exception_message: Message to use for the exception. Formatted
                                  with ``name``
        :throws: :class:`JenkinsException` whenever the view does not exist
        '''
        if not self.view_exists(name):
            raise JenkinsException(exception_message % name)

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
        self.jenkins_open(Request(
            self.server + DELETE_VIEW % self._get_encoded_params(locals()),
            b''))
        if self.view_exists(name):
            raise JenkinsException('delete[%s] failed' % (name))

    def create_view(self, name, config_xml):
        '''Create a new Jenkins view

        :param name: Name of Jenkins view, ``str``
        :param config_xml: config file text, ``str``
        '''
        if self.view_exists(name):
            raise JenkinsException('view[%s] already exists' % (name))

        self.jenkins_open(Request(
            self.server + CREATE_VIEW % self._get_encoded_params(locals()),
            config_xml.encode('utf-8'), DEFAULT_HEADERS))
        self.assert_view_exists(name, 'create[%s] failed')

    def reconfig_view(self, name, config_xml):
        '''Change configuration of existing Jenkins view.

        To create a new view, see :meth:`Jenkins.create_view`.

        :param name: Name of Jenkins view, ``str``
        :param config_xml: New XML configuration, ``str``
        '''
        reconfig_url = self.server + CONFIG_VIEW % self._get_encoded_params(locals())
        self.jenkins_open(Request(reconfig_url, config_xml.encode('utf-8'),
                                  DEFAULT_HEADERS))

    def get_view_config(self, name):
        '''Get configuration of existing Jenkins view.

        :param name: Name of Jenkins view, ``str``
        :returns: view configuration (XML format)
        '''
        request = Request(self.server + CONFIG_VIEW % self._get_encoded_params(locals()))
        return self.jenkins_open(request)
