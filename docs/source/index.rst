.. pyoauth documentation master file, created by
   sphinx-quickstart on Thu Jun 23 23:23:49 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. include:: global.rst.inc

PyOAuth
=======

A Python library that implements the OAuth protocol for clients and servers.

Getting the library
---------------------

::

    $ pip install pyoauth

or

::

    $ git clone git://github.com/gorakhargosh/pyoauth.git
    $ cd pyoauth
    $ python setup.py install


About the implementation
------------------------
This library implements version 1.0 of the OAuth protocol as per
the RFC5849_ specification, which supersedes any previous versions of the
protocol.

Client classes do not send HTTP requests but implement enough of the
OAuth protocol to help you build request proxies that can be used to send actual
HTTP requests. In essence, it implements OAuth 1.0 and nothing else.
This is a very conscious decision by the library authors. It allows
framework authors and API users to use the library without pulling in
unnecessary dependencies which may not work on their platform of choice.
For example, you can use any of httplib2_, tornado_, webapp2_, or django_ to
send HTTP requests built with this library.

Wherever possible the implementation tries to warn you about problems you may
encounter when processing or building OAuth requests by using a fail-fast
approach—we try to tell you as much about the problem as possible. For
example, OAuth relies on the availability of SSL to communicate securely, and
therefore, the library checks whether the OAuth endpoint URLs you specify
use SSL. By default, the library prohibits you from using non https URLs
for OAuth endpoint URLs, but you can change this behavior to suit your needs.

Signature methods
~~~~~~~~~~~~~~~~~
All the signature methods mentioned in the OAuth specification have been
implemented by this library, namely:

1. PLAINTEXT
2. HMAC-SHA1
3. RSA-SHA1

However, the RSA-SHA1 signature method relies on the availability of
third-party libraries like PyCrypto_ or M2Crypto_.

RSA-SHA1 requirements
*********************
The RSA-SHA1 signature methods accept PEM-encoded X.509 certificates,
RSA public keys, and RSA private keys. The validity of the X.509 certificates
will not be verified by any of those routines. You must ensure the validity of
certificates when you accept them by using other utility methods provided by
this library or by other means.

For a quick rundown about these certificates and keys, please read
:ref:`using-rsa-sha1`.


User Guides
===========

.. toctree::
   :maxdepth: 2

   guides/oauth1
   guides/rsa_sha1

API Documentation
=================

.. toctree::
   :maxdepth: 2

   api/protocol
   api/oauth1



Contribute
==========
Found a bug in or want a feature added to |project_name|?
You can fork the official `code repository`_ or file an issue ticket
at the `issue tracker`_. You may also want to refer to :ref:`hacking` for
information about contributing code or documentation to |project_name|.

.. toctree::
   :maxdepth: 2

   hacking

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

