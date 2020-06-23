.. _security guide:

Security Guide
==============

This security guide applies to the Data Attribute Recommendation Python SDK only.
In addition to this document, please carefully consider the `Security Guide  for the
Data Attribute Recommendation service`_ itself.

This guide makes two recommendations to keep your usage of the SDK secure:

* Keep your service keys secret
* Keep your operating system, Python and dependencies up to date

.. _Security Guide  for the Data Attribute Recommendation service: https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/3cb3e86f07164272bf3c3dea2a55a2a5.html

Keeping service keys secret
***************************

A service key for the Data Attribute Recommendation service gives full access
to all data inside the service instances.

Consider the following security aspects:

:Availability: A key holder can delete training data,
               remove models or deployments

:Confidentiality: A key holder can inspect DatasetSchemas and execute
                  inference requests

:Integrity: A key holder can upload training data or cause high costs by deploying
            models and executing inference requests.

To prevent your key from falling into the wrong hands, note the following items:

* Never copy and paste your service key into your Python code

    * Avoid committing your key to public source code hosting such as Github.

* Avoid storing unencrypted keys. Instead, store service keys
  in an encrypted, secure storage.

    * There are python libraries available to easily and safely retrieve keys from your
      secure storage and use them in your project.
    * Modern operating systems typically come with a password manager built in, which
      can also be used in Python.

Keep the environment up to date
*******************************

Keep your operating system and your Python installation always up to date
with the latest security patches.

The Data Attribute Recommendation service uses HTTPS for communication.

With an outdated operating system or Python environment, it may be easier
for a hypothetical man-in-the-middle attacker to find out the service key you are
using or otherwise intercept or interfere with your communication with the Data Attribute
Recommendation service.

To avoid this possibility, two properties should hold:

* The SDK should authenticate the remote side of the connection
* The connection itself should use high-quality cryptography and be secure

The SDK relies on the `requests`_ library to handle both aspects of the encrypted
HTTPS communication. Note that the SDK will reject non-HTTPS URLs.

.. _requests: https://requests.readthedocs.io/en/master/

Internally, the ``requests`` library uses the ``certifi`` library as a source of root `CA
certificates`_. These are used to validate the TLS certificate presented by the remote
server.
The ``certifi`` library can and should be updated independently, as recommended
by the `requests`_ documentation.
Additionally, the ``requests`` packages also verifies that the host name inside the
certificate `matches the host name`_ used inside the service key.


.. _matches the host name: https://requests.readthedocs.io/en/v2.9.1/user/advanced/#ssl-cert-verification
.. _CA certificates: https://requests.readthedocs.io/en/v2.9.1/user/advanced/#ca-certificates

To actually establish the encrypted HTTPS connection, ``requests`` uses the
``urllib3`` package.
The ``urllib3`` package will by default use the SSL implementation shipped with your
version of Python. Newer Python versions or even just the same version of Python linked
against an improved version of the underlying OpenSSL library can provide important
security fixes. Having an up-to-date system is thus crucial to having the most
cryptographically secure HTTPS connection.

From this rather technical discussion, the following takeaway:
**always apply security updates across your entire environment.**

To update all Python packages used in your environment, consider
the combination of ``pip list --outdated`` and ``pip install --upgrade``. Note
that the SDK itself only explicitly depends on ``requests``. The other packages
mentioned are installed as dependencies and must also be kept up to date.
The SDK itself can be expected to work with newer version of the ``requests``
package, as expressed by the "greater-than" dependency declaration ``requests>=2.20.0``.

For updates to your operating system or your Python stack, please contact
the respective vendor.