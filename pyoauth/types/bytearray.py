#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Released into public domain.

"""
:module: pyoauth.crypto.utils.bytearray
:synopsis: Byte arrays.

Functions:
----------
.. autofunction:: bytearray_create
.. autofunction:: bytearray_create_zeros
.. autofunction:: bytearray_concat
.. autofunction:: bytearray_to_bytes
.. autofunction:: bytes_to_bytearray
.. autofunction:: generate_random_bytearray
.. autofunction:: bytearray_to_long
.. autofunction:: long_to_bytearray
.. autofunction:: bytearray_base64_decode
.. autofunction:: bytearray_base64_encode

"""

from array import array
from pyoauth.crypto.utils import byte_count, base64_encode, base64_decode
from pyoauth.crypto.utils.prng import generate_random_bytes


def bytearray_create(sequence):
    """
    Creates a byte array from a given sequence.

    :param sequence:
        The sequence from which a byte array will be created.
    :returns:
        A byte array.
    """
    return array('B', sequence)


def bytearray_create_zeros(count):
    """
    Creates a zero-filled byte array of with ``count`` bytes.

    :param count:
        The number of zero bytes.
    :returns:
        Zero-filled byte array.
    """
    return array('B', [0] * count)


def bytearray_concat(byte_array1, byte_array2):
    """
    Concatenates two byte arrays.

    :param byte_array1:
        Byte array 1
    :param byte_array2:
        Byte array 2
    :returns:
        Concatenated byte array.
    """
    return byte_array1 + byte_array2


def bytearray_to_bytes(byte_array):
    """
    Converts a byte array into a string.

    :param byte_array:
        The byte array.
    :returns:
        String.
    """
    return byte_array.tostring()


def bytes_to_bytearray(byte_string):
    """
    Converts a string into a byte array.

    :param byte_string:
        String value.
    :returns:
        Byte array.
    """
    byte_array = bytearray_create_zeros(0)
    byte_array.fromstring(byte_string)
    return byte_array


def generate_random_bytearray(count):
    """
    Generates a random byte array.

    :param count:
        The number of bytes.
    :returns:
        A random byte array.
    """
    return bytes_to_bytearray(generate_random_bytes(count))


def bytearray_to_long(byte_array):
    """
    Converts a byte array to long.

    :param byte_array:
        The byte array.
    :returns:
        Long.
    """
    total = 0L
    multiplier = 1L
    for count in range(len(byte_array)-1, -1, -1):
        byte_val = byte_array[count]
        total += multiplier * byte_val
        multiplier *= 256
    return total


def long_to_bytearray(num):
    """
    Converts a long into a byte array.

    :param num:
        Long value
    :returns:
        Long.
    """
    bytes_count = byte_count(num)
    byte_array = bytearray_create_zeros(bytes_count)
    for count in range(bytes_count - 1, -1, -1):
        byte_array[count] = int(num % 256)
        num >>= 8
    return byte_array


def bytearray_base64_decode(encoded):
    """
    Converts a base-64 encoded value into a byte array.

    :param encoded:
        The base-64 encoded value.
    :returns:
        Byte array.
    """
    return bytes_to_bytearray(base64_decode(encoded))


def bytearray_base64_encode(byte_array):
    """
    Base-64 encodes a byte array.

    :param byte_array:
        The byte array.
    :returns:
        Base-64 encoded byte array without newlines.
    """
    return base64_encode(bytearray_to_bytes(byte_array))