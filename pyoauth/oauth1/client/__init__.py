#!/usr/bin/env python
# -*- coding: utf-8 -*-
# OAuth 1.0 Client.
#
# Copyright (C) 2011 Yesudeep Mangalapilly <yesudeep@gmail.com>
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

"""
:module: pyoauth.oauth1.client
:synopsis: Implements an OAuth 1.0 client.

.. autoclass:: Client
   :members:
   :show-inheritance:
"""

import logging
from pyoauth.error import IllegalArgumentError, \
    InvalidHttpResponseError, \
    HttpError, \
    InvalidSignatureMethodError, \
    InvalidAuthorizationHeaderError, \
    InvalidContentTypeError, InvalidHttpRequestError

from pyoauth.http import RequestProxy, CONTENT_TYPE_FORM_URLENCODED
from pyoauth.oauth1 import \
    Credentials, \
    SIGNATURE_METHOD_HMAC_SHA1, \
    SIGNATURE_METHOD_RSA_SHA1, \
    SIGNATURE_METHOD_PLAINTEXT
from pyoauth.url import \
    oauth_url_sanitize, \
    request_protocol_params_sanitize, \
    query_params_sanitize, \
    url_add_query, \
    url_append_query, \
    parse_qs, query_append, is_valid_callback_url
from pyoauth.protocol import generate_nonce, \
    generate_timestamp, \
    generate_hmac_sha1_signature, \
    generate_rsa_sha1_signature, \
    generate_plaintext_signature, \
    generate_normalized_authorization_header_value


SIGNATURE_METHOD_MAP = {
    SIGNATURE_METHOD_HMAC_SHA1: generate_hmac_sha1_signature,
    SIGNATURE_METHOD_RSA_SHA1: generate_rsa_sha1_signature,
    SIGNATURE_METHOD_PLAINTEXT: generate_plaintext_signature,
}


class Client(object):
    """
    OAuth 1.0 Client.

    :param client_credentials:
        Client (consumer) credentials.
    :param temporary_credentials_request_uri:
        OAuth request token URI.

        Any query parameters starting with ``oauth_`` will be excluded from
        the URL. All OAuth parameters must be specified in their respective
        requests.

        .. NOTE::
            Must use SSL/TLS.

            See http://tools.ietf.org/html/rfc5849#section-2.1
    :param resource_owner_authorization_uri:
        OAuth authorization URI.

        Any query parameters starting with ``oauth_`` will be excluded from
        the URL. All OAuth parameters must be specified in their respective
        requests.
    :param token_request_uri:
        OAuth access token request URI.

        Any query parameters starting with ``oauth_`` will be excluded from
        the URL. All OAuth parameters must be specified in their respective
        requests.

        .. NOTE::
            Must use SSL/TLS.

            See http://tools.ietf.org/html/rfc5849#section-2.3
    :param use_authorization_header:
        ``True`` (default) to use the HTTP Authorization header to pass OAuth
        parameters; ``False`` will force using the URL query string or
        the entity-body of a request.

        Using the HTTP Authorization header is preferable for many reasons
        including:

        1. Keeps your server request logs clean and readable.

        2. Separates any protocol-specific parameters from server or
           application-specific parameters.

        3. Debugging OAuth problems is easier.

        However, not all OAuth servers may support this feature. Therefore,
        you can set this to ``False`` for use with such services.
    :param authorization_header_param_delimiter:
        The delimiter used to separate header value parameters.
        According to the Specification, this must be a comma ``,``. However,
        certain services like Yahoo! use ``&`` instead. Comma is default.

            See https://github.com/oauth/oauth-ruby/pull/12

    """
    def __init__(self,
                 client_credentials,
                 temporary_credentials_request_uri,
                 token_credentials_request_uri,
                 resource_owner_authorization_uri,
                 resource_owner_authentication_uri=None,
                 use_authorization_header=True,
                 authorization_header_param_delimiter=","):
        """
        Creates an instance of an OAuth 1.0 client.
        """
        self._client_credentials = client_credentials
        self._temporary_credentials_request_uri = \
            oauth_url_sanitize(temporary_credentials_request_uri,
                               force_secure=True)
        self._resource_owner_authorization_uri = \
            oauth_url_sanitize(resource_owner_authorization_uri,
                               force_secure=False)
        self._token_credentials_request_uri = \
            oauth_url_sanitize(token_credentials_request_uri,
                               force_secure=True)
        if resource_owner_authentication_uri:
            self._resource_owner_authentication_uri = \
                oauth_url_sanitize(resource_owner_authentication_uri,
                                   force_secure=False)
        else:
            self._resource_owner_authentication_uri = ""
        self._use_authorization_header = use_authorization_header
        self._authorization_header_param_delimiter = authorization_header_param_delimiter

    @property
    def oauth_version(self):
        """Must return ``"1.0"`` (unless for compatibility, in which case,
        you are all by yourself.)"""
        return "1.0"

    def build_temporary_credentials_request(self,
                                            method="POST",
                                            payload_params=None,
                                            headers=None,
                                            realm=None,
                                            oauth_signature_method=SIGNATURE_METHOD_HMAC_SHA1,
                                            oauth_callback="oob",
                                            **extra_oauth_params):
        """
        Builds an OAuth request for temporary credentials.

        :param method:
            HTTP request method. Default POST.
        :param payload_params:
            A dictionary of payload parameters. These will be serialized
            into the URL or the entity-body depending on the HTTP request method.
            These must not include any parameters starting with ``oauth_``. Any
            of these parameters with names starting with the ``oauth_`` prefix
            will be ignored.
        :param headers:
            A dictionary of headers that will be passed along with the request.
            Must not include the "Authorization" header.
        :param realm:
            The value to use for the realm parameter in the Authorization HTTP
            header. It will be excluded from the base string, however.
        :param oauth_signature_method:
            One of:
            1. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_HMAC_SHA1`
            2. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_RSA_SHA1`
            3. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_PLAINTEXT`
        :param oauth_callback:
            A callback URL that you want the server to call when done
            with your requests.
        :param extra_oauth_params:
            Any additional oauth parameters you would like to include.
            The parameter names must begin with ``oauth_``. Any other parameters
            with names that do not begin with this prefix will be ignored.
        :returns:
            An instance of :class:`pyoauth.http.RequestProxy`.
        """
        if not is_valid_callback_url(oauth_callback):
            raise ValueError("`oauth_callback` parameter value is invalid: `%r`" % (oauth_callback, ))

        return self._build_request(method=method,
                                   url=self._temporary_credentials_request_uri,
                                   payload_params=payload_params,
                                   headers=headers,
                                   realm=realm,
                                   oauth_signature_method=oauth_signature_method,
                                   oauth_callback=oauth_callback,
                                   **extra_oauth_params)

    def get_authorization_url(self, temporary_credentials, **query_params):
        """
        Calculates the authorization URL to which the user will be (re)directed.

        :param temporary_credentials:
            Temporary credentials obtained after parsing the response to
            the temporary credentials request.
        :param query_params:
            Additional query parameters that you would like to include
            into the authorization URL. Parameters beginning with the ``oauth_``
            prefix will be ignored.
        """
        url = self._resource_owner_authorization_uri
        if query_params:
            query_params = query_params_sanitize(query_params)
            url = url_append_query(url, query_params)
        # So that the "oauth_token" appears LAST.
        return url_append_query(url, {
            "oauth_token": temporary_credentials.identifier,
        })

    def get_authentication_url(self, temporary_credentials, **query_params):
        """
        Calculates the automatic authentication redirect URL to which the
        user will be (re)directed.

        :param temporary_credentials:
            Temporary credentials obtained after parsing the response to
            the temporary credentials request.
        :param query_params:
            Additional query parameters that you would like to include
            into the authorization URL. Parameters beginning with the ``oauth_``
            prefix will be ignored.
        """
        url = self._resource_owner_authentication_uri
        if not url:
            raise NotImplementedError("Service does not support automatic authentication redirects.")
        if query_params:
            query_params = query_params_sanitize(query_params)
            url = url_append_query(url, query_params)
        # So that the "oauth_token" appears LAST.
        return url_append_query(url, {
            "oauth_token": temporary_credentials.identifier,
        })


    def build_token_credentials_request(self,
                                        temporary_credentials,
                                        oauth_verifier,
                                        method="POST",
                                        payload_params=None,
                                        headers=None,
                                        realm=None,
                                        oauth_signature_method=SIGNATURE_METHOD_HMAC_SHA1,
                                        **extra_oauth_params):
        """
        Builds an OAuth request instance for token credentials from the OAuth
        server.

        :param temporary_credentials:
            Temporary credentials obtained from the response to the
            request built by
            :func:`Client.build_temporary_credentials_request`.
        :param oauth_verifier:
            OAuth verification string sent by the server to your callback URI
            or input by the user into your application.
        :param method:
            The HTTP method to use. Default POST.
        :param payload_params:
            A dictionary of payload parameters. These will be serialized
            into the URL or the entity-body depending on the HTTP request method.
            These must not include any parameters starting with ``oauth_``. Any
            of these parameters with names starting with the ``oauth_`` prefix
            will be ignored.
        :param headers:
            A dictionary of headers that will be passed along with the request.
            Must not include the "Authorization" header.
        :param realm:
            The value to use for the realm parameter in the Authorization HTTP
            header. It will be excluded from the base string, however.
        :param oauth_signature_method:
            One of:
            1. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_HMAC_SHA1`
            2. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_RSA_SHA1`
            3. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_PLAINTEXT`
        :param extra_oauth_params:
            Any additional oauth parameters you would like to include.
            The parameter names must begin with ``oauth_``. Any other parameters
            with names that do not begin with this prefix will be ignored.
        :returns:
            An instance of :class:`pyoauth.http.RequestProxy`.
        """
        if "oauth_callback" in extra_oauth_params:
            raise IllegalArgumentError("`oauth_callback` is reserved for use with temporary credentials request only.")

        return self._build_request(method=method,
                                   url=self._token_credentials_request_uri,
                                   payload_params=payload_params,
                                   headers=headers,
                                   token_or_temporary_credentials=temporary_credentials,
                                   realm=realm,
                                   oauth_signature_method=oauth_signature_method,
                                   oauth_verifier=oauth_verifier,
                                   **extra_oauth_params)

    def build_resource_request(self,
                               token_credentials,
                               method,
                               url,
                               payload_params=None,
                               headers=None,
                               realm=None,
                               oauth_signature_method=SIGNATURE_METHOD_HMAC_SHA1,
                               **extra_oauth_params):
        """
        Builds an OAuth request instance for token credentials from the OAuth
        server.

        :param token_credentials:
            Temporary credentials obtained from the response to the
            request built by
            :func:`Client.build_temporary_credentials_request`.
        :param method:
            The HTTP method to use.
        :param url:
            The HTTP URL to which the resource request must be sent.
        :param payload_params:
            A dictionary of payload parameters. These will be serialized
            into the URL or the entity-body depending on the HTTP request method.
            These must not include any parameters starting with ``oauth_``. Any
            of these parameters with names starting with the ``oauth_`` prefix
            will be ignored.
        :param headers:
            A dictionary of headers that will be passed along with the request.
            Must not include the "Authorization" header.
        :param realm:
            The value to use for the realm parameter in the Authorization HTTP
            header. It will be excluded from the base string, however.
        :param oauth_signature_method:
            One of:
            1. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_HMAC_SHA1`
            2. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_RSA_SHA1`
            3. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_PLAINTEXT`
        :param extra_oauth_params:
            Any additional oauth parameters you would like to include.
            The parameter names must begin with ``oauth_``. Any other parameters
            with names that do not begin with this prefix will be ignored.
        :returns:
            An instance of :class:`pyoauth.http.RequestProxy`.
        """
        if "oauth_callback" in extra_oauth_params:
            raise IllegalArgumentError("`oauth_callback` is reserved for use with temporary credentials request only.")

        return self._build_request(method=method,
                                   url=url,
                                   payload_params=payload_params,
                                   headers=headers,
                                   realm=realm,
                                   token_or_temporary_credentials=token_credentials,
                                   oauth_signature_method=oauth_signature_method,
                                   **extra_oauth_params)

    def check_verification_code(self, temporary_credentials, oauth_token, oauth_verifier):
        """
        When the OAuth 1.0 server redirects the resource owner to your
        callback URL, it will attach two parameters to the query string.

        1. ``oauth_token``: Must match your temporary credentials identifier.
        2. ``oauth_verifier``: Server-generated verification code that you will
           use in the next step--that is requesting token credentials.

        :param temporary_credentials:
            Temporary credentials
        :param oauth_token:
            The value of the ``oauth_token`` parameter as obtained
            from the server redirect.
        :param oauth_verifier:
            The value of the ``oauth_verifier`` parameter as obtained
            from the server redirect.
        """
        if temporary_credentials.identifier != oauth_token:
            raise InvalidHttpRequestError("OAuth token returned in callback query `%r` does not match temporary credentials: `%r`" % (oauth_token, temporary_credentials.identifer,))
        return oauth_verifier

    def parse_temporary_credentials_response(self, response):
        """
        Parses the entity-body of the OAuth server response to an OAuth
        temporary credentials request.

        :param response:
            An instance of :class:`pyoauth.http.ResponseProxy`.
        :returns:
            A tuple of the form::

                (parameter dictionary, pyoauth.oauth1.Credentials instance)
        """
        params, credentials = self._parse_credentials_response(response)
        callback_confirmed = params.get("oauth_callback_confirmed", [""])[0].lower()
        if callback_confirmed != "true":
            raise ValueError("Invalid OAuth server response -- `oauth_callback_confirmed` MUST be set to `true`.")
        return params, credentials

    def parse_token_credentials_response(self, response):
        """
        Parses the entity-body of the OAuth server response to an OAuth
        token credentials request.

        :param response:
            An instance of :class:`pyoauth.http.ResponseProxy`.
        :returns:
            A tuple of the form::

                (parameter dictionary, pyoauth.oauth1.Credentials instance)
        """
        return self._parse_credentials_response(response)

    def _parse_credentials_response(self, response):
        """
        Parses the entity-body of the OAuth server response to an OAuth
        credential request.

        :param response:
            An instance of :class:`pyoauth.http.ResponseProxy`.
        :returns:
            A tuple of the form::

                (parameter dictionary, pyoauth.oauth1.Credentials instance)
        """
        if not response.status_code:
            raise InvalidHttpResponseError("Invalid status code: `%r`" % (response.status_code, ))
        if not response.status:
            raise InvalidHttpResponseError("Invalid status message: `%r`" % (response.status, ))
        if not response.payload:
            raise InvalidHttpResponseError("Body is invalid or empty: `%r`" % (response.payload, ))
        if not response.headers:
            raise InvalidHttpResponseError("Headers are invalid or not specified: `%r`" % (response.headers, ))

        if response.error:
            raise HttpError("Could not fetch credentials: HTTP %d - %s" % (response.status_code, response.status,))
        # The response body must be URL encoded.
        if not response.is_body_form_urlencoded():
            raise InvalidContentTypeError("OAuth credentials server response must have Content-Type: `%s`" % (CONTENT_TYPE_FORM_URLENCODED, ))

        params = parse_qs(response.payload)
        return params, Credentials(identifier=params["oauth_token"][0],
                                   shared_secret=params["oauth_token_secret"][0])

    def _build_request(self,
                      method,
                      url,
                      payload_params=None,
                      headers=None,
                      token_or_temporary_credentials=None,
                      realm=None,
                      oauth_signature_method=SIGNATURE_METHOD_HMAC_SHA1,
                      **extra_oauth_params):
        """
        Builds an OAuth request.

        :param method:
            HTTP request method.
        :param url:
            The OAuth request URI.
        :param payload_params:
            A dictionary of payload parameters. These will be serialized
            into the URL or the entity-body depending on the HTTP request method.
            These must not include any parameters starting with ``oauth_``. Any
            of these parameters with names starting with the ``oauth_`` prefix
            will be ignored.
        :param headers:
            A dictionary of headers that will be passed along with the request.
            Must not include the "Authorization" header.
        :param realm:
            The value to use for the realm parameter in the Authorization HTTP
            header. It will be excluded from the request signature.
        :param oauth_signature_method:
            One of:
            1. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_HMAC_SHA1`
            2. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_RSA_SHA1`
            3. :attr:`pyoauth.oauth1.SIGNATURE_METHOD_PLAINTEXT`
        :param extra_oauth_params:
            Any additional oauth parameters you would like to include.
            The parameter names must begin with ``oauth_``. Any other parameters
            with names that do not begin with this prefix will be ignored.
        :returns:
            An instance of :class:`pyoauth.http.Request`.
        """
        method = method.upper()
        headers = headers or {}
        realm = realm or ""

        if oauth_signature_method not in SIGNATURE_METHOD_MAP:
            raise InvalidSignatureMethodError("Invalid signature method specified: `%r`" % (oauth_signature_method,))

        # Required OAuth protocol parameters.
        # See Making Requests (http://tools.ietf.org/html/rfc5849#section-3.1)
        oauth_params = dict(
            oauth_consumer_key=self._client_credentials.identifier,
            oauth_signature_method=oauth_signature_method,
            oauth_timestamp=generate_timestamp(),
            oauth_nonce=generate_nonce(),
            oauth_version=self.oauth_version,
        )
        if token_or_temporary_credentials:
            oauth_params["oauth_token"] = token_or_temporary_credentials.identifier

        if "_test_force_exclude_oauth_version" in extra_oauth_params:
            del oauth_params["oauth_version"]

        # Filter and add additional OAuth parameters.
        _force_override_reserved_oauth_params_for_tests = "_test_force_override_reserved_oauth_params" in extra_oauth_params
        extra_oauth_params = request_protocol_params_sanitize(extra_oauth_params)
        reserved_oauth_params = (
            "oauth_signature",     # Calculated from given parameters.
            "oauth_nonce",         # System-generated.
            "oauth_timestamp",     # System-generated.
            "oauth_consumer_key",  # Provided when creating the client instance.
            "oauth_version",       # Optional but MUST be set to "1.0" according to spec.
            "oauth_token",         # Determined from the token or temporary credentials.
        )
        for k, v in extra_oauth_params.items():
            if not _force_override_reserved_oauth_params_for_tests and k in reserved_oauth_params:
                # Don't override these required system-generated protocol parameters.
                raise IllegalArgumentError("Cannot override system-generated protocol parameter `%r`." % k)
            else:
                if k in oauth_params:
                    # Warn when an existing protocol parameter is being
                    # overridden.
                    logging.warning("Overriding existing protocol parameter `%r`=`%r` with `%r`=`%r`",
                                    k, oauth_params[k], k, v[0])
                oauth_params[k] = v[0]

        # Filter payload parameters for the request.
        payload_params = query_params_sanitize(payload_params)

        # I was not entirely certain about whether PUT payload
        # params should be included in the signature or not.
        # Here is why:
        #
        #    http://groups.google.com/group/oauth/browse_thread/thread/fdc0b11f2c4a8dc3/
        #
        # http://tools.ietf.org/html/rfc5849#appendix-A
        # However, Appendix A in the RFC specification clarifies this point.
        # form URL encoded entity bodies in a request using any HTTP verb
        # must be part of the base string used for the signature.
        # Therefore, do NOT exclude payload params from the signature URL
        # when the PUT HTTP method is used.
        #
        #if method == "PUT":
        #     signature_url = url
        #else:
        signature_url = url_add_query(url, payload_params)

        # Determine the request's OAuth signature.
        oauth_params["oauth_signature"] = self._sign_request_data(oauth_signature_method,
                                                                  method, signature_url, oauth_params,
                                                                  token_or_temporary_credentials)

        # Build request data now.
        # OAuth parameters and any parameters starting with the ``oauth_``
        # must be included only in ONE of these three locations:
        #
        # 1. Authorization header.
        # 2. Request URI query string.
        # 3. Request entity body.
        #
        # See Parameter Transmission (http://tools.ietf.org/html/rfc5849#section-3.6)
        if "Authorization" in headers:
            raise InvalidAuthorizationHeaderError("Authorization field is already present in headers: `%r`" % (headers, ))
        if self._use_authorization_header:
            auth_header_value = \
                generate_normalized_authorization_header_value(oauth_params,
                                                          realm=realm,
                                                          param_delimiter=self._authorization_header_param_delimiter)
            headers["Authorization"] = auth_header_value
            # Empty the params if using authorization so that they are not
            # included multiple times in a request below.
            oauth_params = None

        if method == "GET":
            request_url = url_add_query(url, payload_params)
            request_url = url_append_query(request_url, oauth_params)
            payload = ""
        else:
            # The payload params are not appended to the OAuth request URL
            # in this case but added to the payload instead.
            request_url = url
            headers["Content-Type"] = CONTENT_TYPE_FORM_URLENCODED
            payload = query_append(payload_params, oauth_params)

        return RequestProxy(method,
                            url=request_url,
                            body=payload,
                            headers=headers)

    def _sign_request_data(self, signature_method,
                           method, url, oauth_params,
                           credentials):
        """
        Generates a signature for the given OAuth request using the credentials
        and the signature method specified.
        """
        sign_func = SIGNATURE_METHOD_MAP[signature_method]
        credentials_shared_secret = credentials.shared_secret if credentials else None
        return sign_func(self._client_credentials.shared_secret,
                         method, url, oauth_params,
                         credentials_shared_secret)
