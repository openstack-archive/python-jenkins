import jenkins
from tests.base import JenkinsTestBase

# Vars in the jenkins module scope that do not need validating
VAR_WHITELIST = ['__doc__',
                 '__file__',
                 '__name__',
                 '__package__',
                 'CRUMB_URL',
                 'DEFAULT_HEADERS',
                 'EMPTY_CONFIG_XML',
                 'EMPTY_FOLDER_XML',
                 'EMPTY_PROMO_CONFIG_XML',
                 'EMPTY_VIEW_CONFIG_XML',
                 'INFO',
                 'LAUNCHER_SSH',
                 'LAUNCHER_COMMAND',
                 'LAUNCHER_JNLP',
                 'LAUNCHER_WINDOWS_SERVICE',
                 'NODE_TYPE',
                 'PROMO_RECONFIG_XML',
                 'RECONFIG_XML']


class JenkinsRestTest(JenkinsTestBase):

    # If there is no filter (depth or tree) we will get an exception
    # on some Jenkins instances
    def test_url_has_filter(self):
        for var in dir(jenkins):
            if var in VAR_WHITELIST:
                continue
            # Misses unicode on 2.x
            val = getattr(jenkins, var)
            if isinstance(val, str):
                # If we end the path in api/json and don't have depth or tree encoded, fail
                self.assertEqual(val.endswith('api/json'), False,
                                 "URLS that end in 'api/json' must be called with depth or tree:" +
                                 "var: [{}] val: [{}]".format(var, val))
