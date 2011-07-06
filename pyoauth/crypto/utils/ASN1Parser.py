#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Class for parsing ASN.1"""
from pyoauth.crypto.utils.compat import *
from pyoauth.crypto.utils.codec import *

#Takes a byte array which has a DER TLV field at its head
class ASN1Parser:
    def __init__(self, bytes):
        p = Parser(bytes)
        p.get(1) #skip Type

        #Get Length
        self.length = self._getASN1Length(p)

        #Get Value
        self.value = p.getFixBytes(self.length)

    #Assuming this is a sequence...
    def getChild(self, which):
        p = Parser(self.value)
        for x in range(which+1):
            markIndex = p.index
            p.get(1) #skip Type
            length = self._getASN1Length(p)
            p.getFixBytes(length)
        return ASN1Parser(p.bytes[markIndex : p.index])

    #Decode the ASN.1 DER length field
    def _getASN1Length(self, p):
        firstLength = p.get(1)
        if firstLength<=127:
            return firstLength
        else:
            lengthLength = firstLength & 0x7F
            return p.get(lengthLength)
