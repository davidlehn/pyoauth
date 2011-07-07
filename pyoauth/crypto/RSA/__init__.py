#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2009 Google Inc.
# Copyright (C) 2011 Yesudeep Mangalapilly
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
:module: pyoauth.crypto.RSA
:synopsis: RSA keys parsing.
:author: Arne Roomann-Kurrik <kurrik@gmail.com>
:author: Yesudeep Mangalapilly <yesudeep@gmail.com>

Classes:
--------
.. autoclass:: RSAPublicKey
"""
import logging

from pyasn1.type import univ
from pyasn1.codec.der import decoder, encoder
from pyoauth.crypto.codec.pemder import pem_to_der_public_key, der_to_pem_public_key, der_to_pem_rsa_private_key, pem_to_der_rsa_private_key, pem_to_der_private_key
from pyoauth.crypto.codec.x509 import SubjectPublicKeyInfo
from pyoauth.crypto.X509 import X509Certificate
from pyoauth.crypto.codec import rsadsa

class RSAPrivateKey(object):
    # http://tools.ietf.org/html/rfc3279 - Section 2.3.1
    _RSA_OID = univ.ObjectIdentifier('1.2.840.113549.1.1.1')

    def __init__(self, key):
        self._key = key
        self._key_asn1, self._private_key_asn1 = self.decode_from_pem_key(key)

    def encode(self):
        return self.encode_to_pem_private_key(self._key_asn1)

    @property
    def private_key(self):
        asn = self._private_key_asn1
        """
        ASN.1 Syntax::

            RSAPrivateKey ::= SEQUENCE {
              version Version,
              modulus INTEGER, -- n
              publicExponent INTEGER, -- e
              privateExponent INTEGER, -- d
              prime1 INTEGER, -- p
              prime2 INTEGER, -- q
              exponent1 INTEGER, -- d mod (p-1)
              exponent2 INTEGER, -- d mod (q-1)
              coefficient INTEGER -- (inverse of q) mod p }

            Version ::= INTEGER
        """
        return dict(
            version          = long(asn.getComponentByName('version')),
            modulus          = long(asn.getComponentByName('modulus')),
            public_exponent  = long(asn.getComponentByName('publicExponent')),
            private_exponent = long(asn.getComponentByName('privateExponent')),
            prime1           = long(asn.getComponentByName('prime1')),
            prime2           = long(asn.getComponentByName('prime2')),
            exponent1        = long(asn.getComponentByName('exponent1')),
            exponent2        = long(asn.getComponentByName('exponent2')),
            coefficient      = long(asn.getComponentByName('coefficient')),
        )


    @classmethod
    def decode_from_pem_key(cls, key):
        keyType = rsadsa.RSAPrivateKey()
        try:
            der = pem_to_der_rsa_private_key(key)
        except Exception, e:
            logging.exception(e)
            der = pem_to_der_private_key(key)

        cover_asn1 = decoder.decode(der)[0]
        if len(cover_asn1) < 1:
            raise ValueError("No RSA private key found after ASN.1 decoding.")

        algorithm = cover_asn1[1][0]
        if algorithm != cls._RSA_OID:
            raise ValueError("Only RSA encryption is currently supported: got algorithm `%r`" % algorithm)
        key_der = bytes(cover_asn1[2])
        key_asn1 = decoder.decode(key_der, asn1Spec=keyType)[0]
        return cover_asn1, key_asn1

    @classmethod
    def encode_to_pem_private_key(cls, key_asn1):
        return der_to_pem_rsa_private_key(encoder.encode(key_asn1))


class RSAPublicKey(object):
    # http://tools.ietf.org/html/rfc3279 - Section 2.3.1
    _RSA_OID = univ.ObjectIdentifier('1.2.840.113549.1.1.1')

    def __init__(self, key):
        self._key = key
        self._key_asn1 = self.decode_from_pem_key(key)

    def encode(self):
        return self.encode_to_pem_key(self._key_asn1)

    @property
    def public_key(self):
        algorithm = self._key_asn1.getComponentByName('algorithm')[0]
        if algorithm != self._RSA_OID:
            raise NotImplementedError("Only RSA encryption is currently supported: got algorithm `%r`" % algorithm)
        return self.parse_public_rsa_key_bits(self._key_asn1.getComponentByName('subjectPublicKey'))

    @classmethod
    def parse_public_rsa_key_bits(cls, public_key_bitstring):
        """
        Extracts the RSA modulus and exponent from a RSA public key bit string.

        :param public_key_bitstring:
            ASN.1 public key bit string.
        :returns:
            Tuple of (modulus, exponent)
        """
        return X509Certificate.parse_public_rsa_key_bits(public_key_bitstring)

    @classmethod
    def decode_from_pem_key(cls, key):
        keyType = SubjectPublicKeyInfo()
        der = pem_to_der_public_key(key)
        key_asn1 = decoder.decode(der, asn1Spec=keyType)[0]
        if len(key_asn1) < 1:
            raise ValueError("No RSA public key found after ASN.1 decoding.")
        return key_asn1

    @classmethod
    def encode_to_pem_key(cls, key_asn1):
        return der_to_pem_public_key(encoder.encode(key_asn1))


TEST_PUBLIC_PEM_KEYS = ("""
-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC0YjCwIfYoprq/FQO6lb3asXrx
LlJFuCvtinTF5p0GxvQGu5O3gYytUvtC2JlYzypSRjVxwxrsuRcP3e641SdASwfr
mzyvIgP08N4S0IFzEURkV1wp/IpH7kH41EtbmUmrXSwfNZsnQRE5SYSOhh+LcK2w
yQkdgcMv11l4KoBkcwIDAQAB
-----END PUBLIC KEY-----
""",
    )

TEST_PUBLIC_KEYS = (
    (126669640320683290646795148731116725859129871317489646670977486626744987251277308188134951784112892388851824395559423655294483477900467304936849324412630428474313221323982004833431306952809970692055204065814102382627007630050419900189287007179961309761697749877767089292033899335453619375029318017462636143731L,
 65537L),
)
