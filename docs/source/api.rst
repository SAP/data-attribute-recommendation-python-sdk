.. _api:


API Documentation
=================

This document describes the Python API available in the SDK. The RESTful API
exposed by the DAR service itself is described in the `SAP Help Portal`_.

The API exposed by the Python SDK either maps directly to a RESTful API
of the service or provides a convenient wrapper around the RESTful API.

.. _SAP Help Portal: https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/b45cf9b24fd042d082c16191aa938c8d.html

This document is split into two sections. The **Public** APIs are classes and methods
that we expect to be the most useful. They interface directly with the Data Attribute
Recommendation service.

The **Internal** APIs are classes and methods which are used internally by the SDK.
A user of the SDK is less likely to deal with them in their day-to-day work. We still
consider documentation for these parts useful to serve as a reference.

This **Internal** API is still part of the API contract: if there is a breaking change
to either the **Internal** or the **Public** API, this will warrant a release
with an updated major version number as required by the `semantic versioning scheme`_.

.. note::

  Before upgrading to a new major version release of the SDK, carefully check
  the `changelog`_ for any breaking changes that might impact you.


.. _semantic versioning scheme: https://semver.org/
.. _changelog: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/CHANGELOG.md

Public API
----------

Workflows
*********

A workflow orchestrates calls over several of the Data Attribute Recommendation's
microservices.

.. automodule:: sap.aibus.dar.client.workflow.model

Data Manager
************

.. automodule:: sap.aibus.dar.client.data_manager_client

.. automodule:: sap.aibus.dar.client.data_manager_constants

Model Manager
*************

.. automodule:: sap.aibus.dar.client.model_manager_client

.. automodule:: sap.aibus.dar.client.model_manager_constants

Inference
*********

.. automodule:: sap.aibus.dar.client.inference_client
.. automodule:: sap.aibus.dar.client.inference_constants

Internal API
------------

The Credentials Module
**********************

.. automodule:: sap.aibus.dar.client.util.credentials

Exceptions
**********

.. automodule:: sap.aibus.dar.client.exceptions

HTTP Connections
****************

.. automodule:: sap.aibus.dar.client.dar_session

.. automodule:: sap.aibus.dar.client.util.http_transport


Base class for client classes
*****************************

.. automodule:: sap.aibus.dar.client.base_client

Utilities
*********

.. automodule:: sap.aibus.dar.client.util.polling
.. automodule:: sap.aibus.dar.client.util.logging
.. automodule:: sap.aibus.dar.client.util.lists