import sys

import kerberos
assert kerberos  # pyflakes
from mock import patch, Mock

from jenkins import urllib_kerb

if sys.version_info < (2, 7):
    import unittest2 as unittest
else:
    import unittest


class KerberosTest(unittest.TestCase):

    @patch('kerberos.authGSSClientResponse')
    @patch('kerberos.authGSSClientStep')
    @patch('kerberos.authGSSClientInit')
    @patch('kerberos.authGSSClientClean')
    def test_simple(self, clean_mock, init_mock, step_mock, response_mock):
        headers_from_server = {'www-authenticate': 'Negotiate xxx'}

        init_mock.side_effect = lambda x: (x, "context")
        response_mock.return_value = "foo"

        parent_mock = Mock()
        parent_return_mock = Mock()
        parent_return_mock.headers = {'www-authenticate': "Negotiate bar"}
        parent_mock.open.return_value = parent_return_mock

        request_mock = Mock()
        h = urllib_kerb.HTTPNegotiateHandler()
        h.add_parent(parent_mock)
        rv = h.http_error_401(request_mock, "", "", "", headers_from_server)

        init_mock.assert_called()
        step_mock.assert_any_call("context", "xxx")
        # verify authGSSClientStep was called for response as well
        step_mock.assert_any_call("context", "bar")
        response_mock.assert_called_with("context")
        request_mock.add_unredirected_header.assert_called_with(
            'Authorization', 'Negotiate %s' % "foo")
        self.assertEqual(rv, parent_return_mock)
        clean_mock.assert_called_with("context")
