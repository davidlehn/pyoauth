#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Written by Bill Janssen. Borrowed from the Python ``ssl`` module.

"""
:module: pyoauth.crypto.codec.pem
:synopsis: PEM/DER conversion utilities.

Functions:
----------
.. autofunction:: pem_to_der
.. autofunction:: der_to_pem
.. autofunction:: cert_time_to_seconds
"""

import time
import textwrap
from functools import partial
from pyoauth.types.codec import base64_decode, base64_encode


CERT_PEM_HEADER = '-----BEGIN CERTIFICATE-----'
CERT_PEM_FOOTER = '-----END CERTIFICATE-----'

PRIVATE_KEY_PEM_HEADER = '-----BEGIN PRIVATE KEY-----'
PRIVATE_KEY_PEM_FOOTER = '-----END PRIVATE KEY-----'

PUBLIC_KEY_PEM_HEADER = '-----BEGIN PUBLIC KEY-----'
PUBLIC_KEY_PEM_FOOTER = '-----END PUBLIC KEY-----'

RSA_PRIVATE_KEY_PEM_HEADER = '-----BEGIN RSA PRIVATE KEY-----'
RSA_PRIVATE_KEY_PEM_FOOTER = '-----END RSA PRIVATE KEY-----'


def cert_time_to_seconds(cert_time):
    """
    Takes a date-time string in standard ASN1_print form
    ("MON DAY 24HOUR:MINUTE:SEC YEAR TIMEZONE") and return
    a Python time value in seconds past the epoch.

    :param cert_time:
        Time value in the certificate.
    :returns:
        Python time value.
    """
    return time.mktime(time.strptime(cert_time, "%b %d %H:%M:%S %Y GMT"))


def pem_to_der(pem_cert_string, pem_header, pem_footer):
    """
    Extracts the DER as a byte sequence out of an ASCII PEM formatted
    certificate or key.

    Taken from the Python SSL module.

    :param pem_cert_string:
        The PEM certificate or key string.
    :param pem_header:
        The PEM header to find.
    :param pem_footer:
        The PEM footer to find.
    """
    # Be a little lenient.
    pem_cert_string = pem_cert_string.strip()
    if not pem_cert_string.startswith(pem_header):
        raise ValueError("Invalid PEM encoding; must start with %s"
                         % pem_header)
    if not pem_cert_string.endswith(pem_footer):
        raise ValueError("Invalid PEM encoding; must end with %s"
                         % pem_footer)
    d = pem_cert_string[len(pem_header):-len(pem_footer)]
    return base64_decode(d)


def der_to_pem(der_cert_bytes, pem_header, pem_footer):
    """
    Takes a certificate in binary DER format and returns the
    PEM version of it as a string.

    Taken from the Python SSL module.

    :param der_cert_bytes:
        A byte string of the DER.
    :param pem_header:
        The PEM header to use.
    :param pem_footer:
        The PEM footer to use.
    """
    # Does what base64.b64encode without the `altchars` argument does.
    f = base64_encode(der_cert_bytes)
    return (pem_header + '\n' +
            textwrap.fill(f, 64) + '\n' +
            pem_footer + '\n')


# Helper functions. Use these instead of using der_to_per and per_to_der.
pem_to_der_private_key = partial(pem_to_der,
                                 pem_header=PRIVATE_KEY_PEM_HEADER,
                                 pem_footer=PRIVATE_KEY_PEM_FOOTER)
pem_to_der_rsa_private_key = partial(pem_to_der,
                                     pem_header=RSA_PRIVATE_KEY_PEM_HEADER,
                                     pem_footer=RSA_PRIVATE_KEY_PEM_FOOTER)
pem_to_der_public_key = partial(pem_to_der,
                                pem_header=PUBLIC_KEY_PEM_HEADER,
                                pem_footer=PUBLIC_KEY_PEM_FOOTER)
pem_to_der_certificate = partial(pem_to_der,
                                 pem_header=CERT_PEM_HEADER,
                                 pem_footer=CERT_PEM_FOOTER)

der_to_pem_private_key = partial(der_to_pem,
                                 pem_header=PRIVATE_KEY_PEM_HEADER,
                                 pem_footer=PRIVATE_KEY_PEM_FOOTER)
der_to_pem_rsa_private_key = partial(der_to_pem,
                                     pem_header=RSA_PRIVATE_KEY_PEM_HEADER,
                                     pem_footer=RSA_PRIVATE_KEY_PEM_FOOTER)
der_to_pem_public_key = partial(der_to_pem,
                                pem_header=PUBLIC_KEY_PEM_HEADER,
                                pem_footer=PUBLIC_KEY_PEM_FOOTER)
der_to_pem_certificate = partial(der_to_pem,
                                 pem_header=CERT_PEM_HEADER,
                                 pem_footer=CERT_PEM_FOOTER)

