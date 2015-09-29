from tests.base import JenkinsTestBase


class UrlHelperTest(JenkinsTestBase):

    def test_url_building(self):
        self.assertEqual(self.j._build_url('api/json'),
                         'http://example.com/api/json')
        self.j.server = 'http://example.com/jenkins/'
        self.assertEqual(self.j._build_url('api/json'),
                         'http://example.com/jenkins/api/json')
        # All of the constant urls correctly omit the trailing slash,
        # but it is possible that a construct like `'/'.join(...)`
        # could result in a leading /
        self.assertEqual(self.j._build_url('/api/json'),
                         'http://example.com/jenkins/api/json')
