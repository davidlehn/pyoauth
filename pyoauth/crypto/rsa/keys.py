#!/usr/bin/env python
# -*- coding: utf-8 -*-

from pyoauth.types.number import long_to_bytes, bytes_to_long


def pkcs1_v1_5_encode(key_size, data):
    """
    Encodes a key using PKCS1's emsa-pkcs1-v1_5 encoding.

    Adapted from paramiko.

    :author:
        Rick Copeland <rcopeland@geek.net>

    :param key_size:
        RSA key size.
    :param data:
        Data
    :returns:
        A blob of data as large as the key's N, using PKCS1's
        "emsa-pkcs1-v1_5" encoding.
    """
    SHA1_DIGESTINFO = '\x30\x21\x30\x09\x06\x05\x2b\x0e\x03\x02\x1a\x05\x00\x04\x14'
    size = len(long_to_bytes(key_size))
    filler = '\xff' * (size - len(SHA1_DIGESTINFO) - len(data) - 3)
    return '\x00\x01' + filler + '\x00' + SHA1_DIGESTINFO + data


class Key(object):
    """
    Abstract class representing an encryption key.
    """
    def __init__(self, key_info, encoded_key, encoding, *args, **kwargs):
        self._key_info = key_info
        self._encoded_key = encoded_key
        self._encoding = encoding

    @property
    def encoded_key(self):
        """
        Returns the original encoded key string.
        """
        return self._encoded_key

    @property
    def encoding(self):
        """
        Returns the original encoding method name of the key.
        """
        return self._encoding

    @property
    def key(self):
        """
        Returns the internal key.
        """
        raise NotImplementedError("Override this property.")

    @property
    def size(self):
        """
        Returns the size of the key (n).
        """
        raise NotImplementedError("Override this property.")

    @property
    def key_info(self):
        """
        Returns the key information parsed from the provided encoded key.
        """
        return self._key_info

    def sign(self, digest):
        """
        Signs a digest with the key.

        :param digest:
            The SHA-1 digest of the data.
        :param encoder:
            The encoding method to use. Default EMSA-PKCS1-v1.5
        :returns:
            Signature byte string.
        """
        return long_to_bytes(self._sign(digest))

    def verify(self, digest, signature_bytes):
        """
        Verifies a signature against that computed by signing the provided
        data.

        :param digest:
            The SHA-1 digest of the data.
        :param signature_bytes:
            The signature raw byte string.
        :param encoder:
            The encoding method to use. Default EMSA-PKCS1-v1.5
        :returns:
            ``True`` if the signature matches; ``False`` otherwise.
        """
        return self._verify(digest, bytes_to_long(signature_bytes))

    def pkcs1_v1_5_sign(self, data):
        """
        Signs a base string using your RSA private key.

        :param data:
            Data byte string.
        :returns:
            Signature.
        """
        digest = pkcs1_v1_5_encode(self.size, data)
        return self.sign(digest)

    def pkcs1_v1_5_verify(self, data, signature_bytes):
        """
        Verifies the signature against a given base string using your
        public key.

        :param data:
            The data to be signed.
        :param signature_bytes:
            Signature to be verified.
        :returns:
            ``True`` if signature matches; ``False`` if verification fails.
        """
        digest = pkcs1_v1_5_encode(self.size, data)
        return self.verify(digest, signature_bytes)

    def _sign(self, digest):
        raise NotImplementedError("Override this method.")

    def _verify(self, digest, signature):
        raise NotImplementedError("Override this method.")


class PrivateKey(Key):
    """
    Abstract private key class.

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
    """
    pass


class PublicKey(Key):
    """
    Abstract public key class.
    """
    pass
