# Copyright (C) 2015 OpenStack Foundation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import logging
import re

import kerberos
from six.moves.urllib import error, request

logger = logging.getLogger(__name__)


class HTTPNegotiateHandler(request.BaseHandler):
    handler_order = 490  # before Digest auth

    def __init__(self, max_tries=5):
        self.krb_context = None
        self.tries = 0
        self.max_tries = max_tries
        self.re_extract_auth = re.compile('.*?Negotiate\s*([^,]*)', re.I)

    def http_error_401(self, req, fp, code, msg, headers):
        logger.debug("INSIDE http_error_401")
        try:
            try:
                krb_req = self._extract_krb_value(headers)
            except ValueError:
                # Negotiate header not found or a similar error
                # we can't handle this, let the next handler have a go
                return None

            if not krb_req:
                # First reply from server (no neg value)
                self.tries = 0
                krb_req = ""
            else:
                if self.tries > self.max_tries:
                    raise error.HTTPError(
                        req.get_full_url(), 401, "Negotiate auth failed",
                        headers, None)

            self.tries += 1
            try:
                krb_resp = self._krb_response(req.host, krb_req)

                req.add_unredirected_header('Authorization',
                                            "Negotiate %s" % krb_resp)

                resp = self.parent.open(req, timeout=req.timeout)
                self._authenticate_server(resp.headers)
                return resp

            except kerberos.GSSError as err:
                try:
                    msg = err.args[1][0]
                except Exception:
                    msg = "Negotiate auth failed"
                logger.debug(msg)
                return None  # let the next handler (if any) have a go

        finally:
            if self.krb_context is not None:
                kerberos.authGSSClientClean(self.krb_context)
                self.krb_context = None

    def _krb_response(self, host, krb_val):
        logger.debug("INSIDE _krb_response")

        _dummy, self.krb_context = kerberos.authGSSClientInit("HTTP@%s" % host)
        kerberos.authGSSClientStep(self.krb_context, krb_val)
        response = kerberos.authGSSClientResponse(self.krb_context)

        logger.debug("kerb auth successful")

        return response

    def _authenticate_server(self, headers):
        logger.debug("INSIDE _authenticate_server")
        try:
            val = self._extract_krb_value(headers)
        except ValueError:
            logger.critical("Server authentication failed."
                            "Auth value couldn't be extracted from headers.")
            return None
        if not val:
            logger.critical("Server authentication failed."
                            "Empty 'Negotiate' value.")
            return None

        kerberos.authGSSClientStep(self.krb_context, val)

    def _extract_krb_value(self, headers):
        logger.debug("INSIDE _extract_krb_value")
        header = headers.get('www-authenticate', None)

        if header is None:
            msg = "www-authenticate header not found"
            logger.debug(msg)
            raise ValueError(msg)

        if "negotiate" in header.lower():
            matches = self.re_extract_auth.search(header)
            if matches:
                return matches.group(1)
            else:
                return ""
        else:
            msg = "Negotiate not in www-authenticate header (%s)" % header
            logger.debug(msg)
            raise ValueError(msg)
