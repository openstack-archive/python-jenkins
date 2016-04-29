import kerberos
assert kerberos  # pyflakes
from mock import patch, Mock
from six.moves.urllib.request import Request
import testtools

from jenkins import urllib_kerb


class KerberosTests(testtools.TestCase):

    @patch('kerberos.authGSSClientResponse')
    @patch('kerberos.authGSSClientStep')
    @patch('kerberos.authGSSClientInit')
    @patch('kerberos.authGSSClientClean')
    def test_http_error_401_simple(self, clean_mock, init_mock, step_mock, response_mock):
        headers_from_server = {'www-authenticate': 'Negotiate xxx'}

        init_mock.side_effect = lambda x: (x, "context")
        response_mock.return_value = "foo"

        parent_mock = Mock()
        parent_return_mock = Mock()
        parent_return_mock.headers = {'www-authenticate': "Negotiate bar"}
        parent_mock.open.return_value = parent_return_mock

        request_mock = Mock(spec=self._get_dummy_request())
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

    @patch('kerberos.authGSSClientResponse')
    @patch('kerberos.authGSSClientStep')
    @patch('kerberos.authGSSClientInit')
    @patch('kerberos.authGSSClientClean')
    def test_http_error_401_gsserror(self, clean_mock, init_mock, step_mock, response_mock):
        headers_from_server = {'www-authenticate': 'Negotiate xxx'}

        init_mock.side_effect = kerberos.GSSError

        h = urllib_kerb.HTTPNegotiateHandler()
        rv = h.http_error_401(Mock(spec=self._get_dummy_request()), "", "", "",
                              headers_from_server)
        self.assertEqual(rv, None)

    @patch('kerberos.authGSSClientResponse')
    @patch('kerberos.authGSSClientStep')
    @patch('kerberos.authGSSClientInit')
    @patch('kerberos.authGSSClientClean')
    def test_http_error_401_empty(self, clean_mock, init_mock, step_mock, response_mock):
        headers_from_server = {}

        h = urllib_kerb.HTTPNegotiateHandler()
        rv = h.http_error_401(Mock(spec=self._get_dummy_request()), "", "", "",
                              headers_from_server)
        self.assertEqual(rv, None)

    @patch('kerberos.authGSSClientResponse')
    @patch('kerberos.authGSSClientStep')
    @patch('kerberos.authGSSClientInit')
    def test_krb_response_simple(self, init_mock, step_mock, response_mock):
        response_mock.return_value = "foo"
        init_mock.return_value = ("bar", "context")
        h = urllib_kerb.HTTPNegotiateHandler()
        rv = h._krb_response("host", "xxx")
        self.assertEqual(rv, "foo")

    @patch('kerberos.authGSSClientResponse')
    @patch('kerberos.authGSSClientStep')
    @patch('kerberos.authGSSClientInit')
    def test_krb_response_gsserror(self, init_mock, step_mock, response_mock):
        response_mock.side_effect = kerberos.GSSError
        init_mock.return_value = ("bar", "context")
        h = urllib_kerb.HTTPNegotiateHandler()
        with testtools.ExpectedException(kerberos.GSSError):
            h._krb_response("host", "xxx")

    @patch('kerberos.authGSSClientStep')
    def test_authenticate_server_simple(self, step_mock):
        headers_from_server = {'www-authenticate': 'Negotiate xxx'}
        h = urllib_kerb.HTTPNegotiateHandler()
        h.krb_context = "foo"
        h._authenticate_server(headers_from_server)
        step_mock.assert_called_with("foo", "xxx")

    @patch('kerberos.authGSSClientStep')
    def test_authenticate_server_empty(self, step_mock):
        headers_from_server = {'www-authenticate': 'Negotiate'}
        h = urllib_kerb.HTTPNegotiateHandler()
        rv = h._authenticate_server(headers_from_server)
        self.assertEqual(rv, None)

    def test_extract_krb_value_simple(self):
        headers_from_server = {'www-authenticate': 'Negotiate xxx'}
        h = urllib_kerb.HTTPNegotiateHandler()
        rv = h._extract_krb_value(headers_from_server)
        self.assertEqual(rv, "xxx")

    def test_extract_krb_value_empty(self):
        headers_from_server = {}
        h = urllib_kerb.HTTPNegotiateHandler()
        with testtools.ExpectedException(ValueError):
            h._extract_krb_value(headers_from_server)

    def test_extract_krb_value_invalid(self):
        headers_from_server = {'www-authenticate': 'Foo-&#@^%:; bar'}
        h = urllib_kerb.HTTPNegotiateHandler()
        with testtools.ExpectedException(ValueError):
            h._extract_krb_value(headers_from_server)

    def _get_dummy_request(self):
        r = Request('http://example.com')
        r.timeout = 10
        return r
