# Software License Agreement (BSD License)
#
# Copyright (c) 2015 Hewlett-Packard Development Company, L.P.
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
# Darragh Bailey <dbailey@hp.com>

import json

import mock
from testscenarios.testcase import TestWithScenarios
import testtools

from jenkins import plugins
from tests.helper import jenkins


dummy_plugin_info = {
    u"active": u'true',
    u"backupVersion": u'null',
    u"bundled": u'true',
    u"deleted": u'false',
    u"dependencies": [],
    u"downgradable": u'false',
    u"enabled": u'true',
    u"hasUpdate": u'true',
    u"longName": u"Dummy Plugin",
    u"pinned": u'false',
    u"shortName": u"dummy",
    u"supportsDynamicLoad": u"MAYBE",
    u"url": u"http://wiki.jenkins-ci.org/display/JENKINS/Dummy",
    u"version": u"1.5"
}


class PluginsTestScenarios(TestWithScenarios, testtools.TestCase):
    scenarios = [
        ('s1', dict(v1='1.0.0', op='__gt__', v2='0.8.0')),
        ('s2', dict(v1='1.0.1alpha', op='__gt__', v2='1.0.0')),
        ('s3', dict(v1='1.0', op='__eq__', v2='1.0.0')),
        ('s4', dict(v1='1.0', op='__eq__', v2='1.0')),
        ('s5', dict(v1='1.0', op='__lt__', v2='1.8.0')),
        ('s6', dict(v1='1.0.1alpha', op='__lt__', v2='1.0.1')),
        ('s7', dict(v1='1.0alpha', op='__lt__', v2='1.0.0')),
        ('s8', dict(v1='1.0-alpha', op='__lt__', v2='1.0.0')),
        ('s9', dict(v1='1.1-alpha', op='__gt__', v2='1.0')),
        ('s10', dict(v1='1.0-SNAPSHOT', op='__lt__', v2='1.0')),
        ('s11', dict(v1='1.0.preview', op='__lt__', v2='1.0')),
        ('s12', dict(v1='1.1-SNAPSHOT', op='__gt__', v2='1.0')),
        ('s13', dict(v1='1.0a-SNAPSHOT', op='__lt__', v2='1.0a')),
    ]

    plugin_info = {
        u"plugins": [
            dummy_plugin_info
        ]
    }

    def setUp(self):
        super(PluginsTestScenarios, self).setUp()

        plugin_info_json = dict(self.plugin_info)
        plugin_info_json[u"plugins"][0][u"version"] = self.v1

        patcher = mock.patch.object(jenkins.Jenkins, 'jenkins_open')
        self.jenkins_mock = patcher.start()
        self.addCleanup(patcher.stop)
        self.jenkins_mock.return_value = json.dumps(plugin_info_json)

    def test_plugin_version_comparison(self):
        """Verify that valid versions are ordinally correct.

        That is, for each given scenario, v1.op(v2)==True where 'op' is the
        equality operator defined for the scenario.
        """
        plugin_name = "Dummy Plugin"
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        plugin_info = j.get_plugins()[plugin_name]
        v1 = plugin_info.get("version")

        op = getattr(v1, self.op)

        self.assertTrue(op(self.v2),
                        msg="Unexpectedly found {0} {2} {1} == False "
                            "when comparing versions!"
                            .format(v1, self.v2, self.op))

    def test_plugin_version_object_comparison(self):
        """Verify use of PluginVersion for comparison

        Verify that converting the version to be compared to the same object
        type of PluginVersion before comparing provides the same result.
        """
        plugin_name = "Dummy Plugin"
        j = jenkins.Jenkins('http://example.com/', 'test', 'test')
        plugin_info = j.get_plugins()[plugin_name]
        v1 = plugin_info.get("version")

        op = getattr(v1, self.op)
        v2 = plugins.PluginVersion(self.v2)

        self.assertTrue(op(v2),
                        msg="Unexpectedly found {0} {2} {1} == False "
                            "when comparing versions!"
                            .format(v1, v2, self.op))


class PluginsTest(testtools.TestCase):

    def test_plugin_equal(self):

        p1 = plugins.Plugin(dummy_plugin_info)
        p2 = plugins.Plugin(dummy_plugin_info)

        self.assertEqual(p1, p2)

    def test_plugin_not_equal(self):

        p1 = plugins.Plugin(dummy_plugin_info)
        p2 = plugins.Plugin(dummy_plugin_info)
        p2[u'version'] = u"1.6"

        self.assertNotEqual(p1, p2)
