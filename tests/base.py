import sys

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class JenkinsTestBase(unittest.TestCase):

    def _check_requests(self, requests):

        for req in requests:
            req[0][0].prepare()
