Welcome to DAR Client's documentation!
======================================

The DAR Client
**************

Features
--------

- Easy to use
- High-level flows on top of the basic DAR APIs
- Fully type annotated for great autocomplete experience
- Supports Python 3.5 up to 3.8

Getting Started
---------------

First, let's train a model with :class:`~sap.aibus.dar.client.flow.create.CreateModel`::

    from sap.aibus.dar.client.workflow.model import ModelCreator

    creator = ModelCreator.construct_from_credentials(
        dar_url='https://data-attribute-recommendation-internalproduction.cfapps.sap.hana.ondemand.com',
        clientid="sb-e52aad05-411c-4b52-a3cc-3d1c162e2f8d!b7898|dar-v3-std!b4321",
        clientsecret="XXXXXXXXXXX",
        uaa_url="https://abcd.authentication.sap.hana.ondemand.com"
    )

    new_schema = {
        "features": [
            {"label": "manufacturer", "type": "CATEGORY"},
            {"label": "description", "type": "TEXT"},
        ],
        "labels": [
            {"label": "category", "type": "CATEGORY"},
            {"label": "subcategory", "type": "CATEGORY"},
        ],
        "name": "bestbuy-category-prediction",
    }

    training_data_stream = open("bestBuy.csv.gz", mode="r")

    resp = creator.create(
        model_template_id="d7810207-ca31-4d4d-9b5a-841a644fd81f",
        dataset_schema=new_schema,
        model_name="bestbuy-category-prediction",
        data_stream=training_data_stream,
    )




Workflows
---------

.. automodule:: sap.aibus.dar.client.workflow.model

Data Manager
------------

.. automodule:: sap.aibus.dar.client.data_manager_client

.. automodule:: sap.aibus.dar.client.data_manager_constants

Model Manager
-------------

.. automodule:: sap.aibus.dar.client.model_manager_client

.. automodule:: sap.aibus.dar.client.model_manager_constants

Inference
----------

.. automodule:: sap.aibus.dar.client.inference_client
.. automodule:: sap.aibus.dar.client.inference_constants



The Credentials Module
**********************

.. automodule:: sap.aibus.dar.client.util.credentials


Exceptions
**********

.. automodule:: sap.aibus.dar.client.exceptions

HTTP
****

.. automodule:: sap.aibus.dar.client.dar_session

.. automodule:: sap.aibus.dar.client.util.http_transport


BASE
****

.. automodule:: sap.aibus.dar.client.base_client

UTIL
****

.. automodule:: sap.aibus.dar.client.util.polling

RETRY
*****

See :ref:`retry`.

SECURITY GUIDE
**************

See :ref:`security guide`.

Table of Contents
=================
..  toctree::
    :maxdepth: 2
    :caption: Contents:

    retry.rst
    security.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
