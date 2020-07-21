.. _index:

Data Attribute Recommendation Python SDK Documentation
======================================================

Features
--------

- Easy to use
- High-level flows on top of the basic Data Attribute Recommendation APIs
- Fully type annotated for great autocomplete experience
- Supports Python 3.5 up to 3.8

Getting Started
---------------

Prerequisites
+++++++++++++

This introduction assumes you have already installed the SDK via:

.. code-block:: shell

  $ pip install data-attribute-recommendation-sdk

Please refer to the main `"Download and Installation" section in the README`_ for
additional installation and troubleshooting guidance.

.. _"Download and Installation" section in the README: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/README.md#download-and-installation

Furthermore, this introduction assumes that you:
* have access to a service instance of the Data Attribute Recommendation service
* have a service key for the service

For more information, please see the `"Requirements" section in the README`_.

.. _"Requirements" section in the README: https://github.com/SAP/data-attribute-recommendation-python-sdk/blob/master/README.md#requirements

The examples below are given for Linux or macOS based system, but should easily
transfer to Windows.

Train a model
++++++++++++++++

As a first step, let's upload a dataset and train a model with
:class:`~sap.aibus.dar.client.flow.create.CreateModel`. The following example
uses a sample dataset based on a BestBuy dataset which contains product meta data along
with the categories for a given product.

.. note::

  Visit the `Concepts`_ page in the official Data Attribute Recommendation documentation
  to learn about Models, Datasets and other terms.

.. _Concepts: https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/fe501df6d9f94361bfea066f9a6f6712.html

Obtain sample dataset
++++++++++++++++++++++++++++

You can download the sample dataset from the `samples repository for the Data Attribute
Recommendation service`_. Be sure to consider the `license of the dataset`_.

.. _samples repository for the Data Attribute Recommendation service: https://github.com/SAP-samples/data-attribute-recommendation-postman-tutorial-sample
.. _license of the dataset: https://github.com/SAP-samples/data-attribute-recommendation-postman-tutorial-sample#data-and-license

To download the dataset, execute:

.. code-block:: shell

  $ curl \
    -o bestBuy.csv \
    'https://raw.githubusercontent.com/SAP-samples/data-attribute-recommendation-postman-tutorial-sample/master/Tutorial_Example_Dataset.csv'
  $ head -n2 bestBuy.csv # look at first two lines
  description,manufacturer,price,level1_category,level2_category,level3_category
  Compatible with select electronic devices; AAA size; DURALOCK Power Preserve technology; 4-pack,Duracell,5.49,Connected Home & Housewares,Housewares,Household Batteries

Prepare service key
+++++++++++++++++++++++++

With the dataset file in place, you will also need to obtain a service key for the
Data Attribute Recommendation service and save it as plain text inside a file named
*dar_service_key.json*. To understand how to create a service key, refer to the
corresponding section `"Creating Service Keys" on the SAP Help Portal`_.

.. _"Creating Service Keys" on the SAP Help Portal: https://help.sap.com/viewer/65de2977205c403bbc107264b8eccf4b/Cloud/en-US/4514a14ab6424d9f84f1b8650df609ce.html

.. note::

  Please ensure that your service key remains confidential
  and consider the information in `security guide`_.

Upload data and train a model
+++++++++++++++++++++++++++++++++++

You should now have two files in place:

* *bestBuy.csv*, which is the data we use to train the model
* *dar_service_key.json*, which contains the credentials used to
  access the Data Attribute Recommendation service.

You are now ready to upload your training data and launch a training job.

.. note::

  Make sure you are still working in the same directory where
  you put the files containing the training data and the key.

Simply open a Python interpreter or your preferred Python IDE
and execute the following code.

.. note::

  Only one model with a given name may exist at a time. If this is not the
  first time you execute the example, you need to change the value of
  the *MODEL_NAME* variable. Further below, you will learn how to delete
  an existing model to free up resources and be able to reuse the name.

.. code-block:: python

    from sap.aibus.dar.client.workflow.model import ModelCreator
    import json
    import pprint

    # Show some output while the script is working
    import logging
    logging.basicConfig(level=logging.INFO)

    MODEL_NAME = "bestbuy-category-prediction"

    # Read file with service key
    with open('dar_service_key.json', 'r') as sk_file:
        sk_data = sk_file.read()

    # Load from file
    json_data = json.loads(sk_data)

    # Create a ModelCreator instance by pass the credentials
    # and the service URL to the
    creator = ModelCreator.construct_from_credentials(
        dar_url=json_data['url'],
        clientid=json_data['uaa']['clientid'],
        clientsecret=json_data['uaa']['clientsecret'],
        uaa_url=json_data['uaa']['url'],
    )

    # Define the DatasetSchema which describes the CSV layout.
    new_schema = {
        "features": [
            {"label": "manufacturer", "type": "CATEGORY"},
            {"label": "description", "type": "TEXT"},
            {"label": "price", "type": "NUMBER"},
        ],
        "labels": [
            {"label": "level1_category", "type": "CATEGORY"},
            {"label": "level2_category", "type": "CATEGORY"},
            {"label": "level3_category", "type": "CATEGORY"},

        ],
        "name": "bestbuy-category-prediction",
    }

    # Load training data
    training_data_stream = open("bestBuy.csv", mode="rb")

    # Upload data and train model
    final_api_response = creator.create(
        model_template_id="d7810207-ca31-4d4d-9b5a-841a644fd81f",
        dataset_schema=new_schema,
        model_name=MODEL_NAME,
        data_stream=training_data_stream,
    )

    pprint.pprint(final_api_response)

When you execute this example, you will have to wait for about 10 minutes (depending
on service load) for the training to succeed.

This example creates a model named **bestbuy-category-prediction**.
The model learns to predict the fields **level1_category**, **level2_category** and
**level3_category** from the **manufacturer**, **description** and **price**
columns in the CSV file.

The script will give detailed output on its progress due to the using
of the **logging.INFO** level. You should see something similar to the following
output (edited for brevity):

::

    INFO:sap.aibus.dar.client.workflow.model.ModelCreator:Creating DatasetSchema.
    INFO:sap.aibus.dar.client.util.credentials.OnlineCredentialsSource:Retrieving token from URL: [..]
    INFO:sap.aibus.dar.client.util.credentials.OnlineCredentialsSource:Got token for clientid [...]
    INFO:sap.aibus.dar.client.workflow.model.ModelCreator:Created dataset schema with id 'a9dae2c5-9902-4268-9031-c351c398f215'
    INFO:sap.aibus.dar.client.workflow.model.ModelCreator:Creating Dataset with name 'bestbuy-category-prediction-b2b39c5d-9883-44ec-853c-af75aeffd1ac'
    INFO:sap.aibus.dar.client.workflow.model.ModelCreator:Created Dataset with id '2579eadb-343f-46f5-b298-61805db393fc'
    INFO:sap.aibus.dar.client.workflow.model.ModelCreator:Uploading data to Dataset '2579eadb-343f-46f5-b298-61805db393fc'
    INFO:sap.aibus.dar.client.workflow.model.ModelCreator:Data uploaded and validated successfully for dataset '2579eadb-343f-46f5-b298-61805db393fc'
    INFO:sap.aibus.dar.client.workflow.model.ModelCreator:Starting training job.
    INFO:sap.aibus.dar.client.workflow.model.ModelCreator:Training finished successfully. Job ID: 'bca5f678-c5d7-453c-af37-69505187dc9b'


The last lines will be the result of ``pprint.pprint(final_api_response)``. This is the response sent by the RESTful API
when querying the model status:

.. code-block:: python

    {
        'createdAt': '2020-07-03T13:25:24+00:00',
        'name': 'bestbuy-category-prediction',
        'validationResult': {
            'accuracy': 0.7949677686677402,
            'f1Score': 0.7969754567454136,
            'precision': 0.8167846008683105,
            'recall': 0.7949677687668955
        }
    }

The training was successful and the *validationResult* indicates that the model will
deliver reasonable performance, even on a small example dataset.

.. note::

    The exact numbers you will see in the *validationResult* will differ
    slightly.


Deploy the model
++++++++++++++++++++


The model has now been successfully trained. Before you can execute inference
requests, you have to deploy the model. This is done using the
:class:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient`.

.. note::

    Deployments can incur costs.


To use the *ModelManagerClient* class, you have to create an instance by passing
the credentials. This interface is identical to the *ModelCreator* used above.

Let's start with an example to list all currently existing models:

.. code-block:: python

    import json
    import logging
    import pprint

    from sap.aibus.dar.client.model_manager_client import ModelManagerClient

    # Show some output while the script is working
    logging.basicConfig(level=logging.INFO)

    MODEL_NAME = "bestbuy-category-prediction"

    # Read file with service key
    with open('dar_service_key.json', 'r') as sk_file:
        sk_data = sk_file.read()

    # Load from file
    json_data = json.loads(sk_data)

    mm_client = ModelManagerClient.construct_from_credentials(
        dar_url=json_data['url'],
        clientid=json_data['uaa']['clientid'],
        clientsecret=json_data['uaa']['clientsecret'],
        uaa_url=json_data['uaa']['url'],
    )

    # Read all models
    model_collection = mm_client.read_model_collection()

    print("There are %s model(s) available." % model_collection['count'])
    print("Listing all known models:")
    print("-" * 20)
    for model_resource in model_collection['models']:
        pprint.pprint(model_resource)
        print("-" * 20)

Executing this script will yield output similar to the following::


    There are 1 model(s) available.
    Listing all known models:
    --------------------
    {
        'createdAt': '2020-07-03T13:25:24+00:00',
        'name': 'bestbuy-category-prediction',
        'validationResult': {
            'accuracy': 0.7949677686677402,
            'f1Score': 0.7969754567454136,
            'precision': 0.8167846008683105,
            'recall': 0.7949677687668955
        }
    }
    --------------------


Besides retrieving the full collection, you can also retrieve individual models:

.. code-block:: python

    MODEL_NAME = "bestbuy-category-prediction"

    model_resource = mm_client.read_model_by_name(MODEL_NAME)
    pprint.pprint(model_resource)


To actually deploy the model, two steps are required:
* create a deployment
* wait for this deployment to succeed

Execute the following script:

.. code-block:: python

    import json
    # Show some output while the script is working
    import logging
    import pprint

    from sap.aibus.dar.client.model_manager_client import ModelManagerClient

    logging.basicConfig(level=logging.INFO)

    MODEL_NAME = "bestbuy-category-prediction"

    # Read file with service key
    with open('dar_service_key.json', 'r') as sk_file:
        sk_data = sk_file.read()

    # Load from file
    json_data = json.loads(sk_data)

    mm_client = ModelManagerClient.construct_from_credentials(
        dar_url=json_data['url'],
        clientid=json_data['uaa']['clientid'],
        clientsecret=json_data['uaa']['clientsecret'],
        uaa_url=json_data['uaa']['url'],
    )

    deployment_resource = mm_client.create_deployment(MODEL_NAME)
    deployment_id = deployment_resource["id"]
    print("Created Deployment for model '%s' with deployment ID '%s'" % (
        MODEL_NAME, deployment_id))

    pprint.pprint(deployment_resource)

    print("Waiting for Deployment to succeed.")
    updated_deployment_resource = mm_client.wait_for_deployment(deployment_resource['id'])
    print("Deployment finished. Final state:")
    pprint.pprint(updated_deployment_resource)




This script will yield the following output (edited for brevity)::

    Created Deployment for model 'bestbuy-category-prediction' with
    deployment ID 'ms-f903c34b-3763-4ec6-9987-1e160849f8d1'
    {
        'deployedAt': None,
        'id': 'ms-f903c34b-3763-4ec6-9987-1e160849f8d1',
        'modelName': 'bestbuy-category-prediction',
        'status': 'PENDING'
    }


The deployment is in status **PENDING** right after creation. The following call to
:meth:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient.wait_for_deployment`.
will poll the deployment until it succeeds.

::

    Deployment finished. Final state:
    {
        'deployedAt': '2020-07-03T13:47:36.527000+00:00',
        'id': 'ms-f903c34b-3763-4ec6-9987-1e160849f8d1',
        'modelName': 'bestbuy-category-prediction',
        'status': 'SUCCEEDED'
    }

The deployment is now in status **SUCCEEDED** and the model can be used for inference
requests.

.. note::

    The :class:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient` additionally
    provides more convenient means to interact with Deployments.
    The :meth:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient.deploy_and_wait`
    method
    combines the :meth:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient.create_deployment`
    and :meth:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient.wait_for_deployment`
    methods into a single call.

    The :meth:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient.ensure_deployment_exists` method
    can be used instead of :meth:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient.create_deployment`
    with the advantage that it will recover from failed deployments automatically.

.. note::

    Consult the documentation for
    :meth:`~sap.aibus.dar.client.model_manager_client.ModelManagerClient.wait_for_deployment` to
    learn about possible error conditions.

Run inference requests against the model
++++++++++++++++++++++++++++++++++++++++++++

Inference requests are performed using the
:class:`~sap.aibus.dar.client.inference_client.InferenceClient`.

The input to the
:meth:`~sap.aibus.dar.client.inference_client.InferenceClient.create_inference_request`
is simply the model name and the list of objects to be classified.

Run the following script to predict the categories for some data:

.. code-block:: python

    import json
    import logging
    import pprint

    from sap.aibus.dar.client.inference_client import InferenceClient

    # Show some output while the script is working
    logging.basicConfig(level=logging.INFO)

    MODEL_NAME = "bestbuy-category-prediction"

    # Read file with service key
    with open('dar_service_key.json', 'r') as sk_file:
        sk_data = sk_file.read()

    # Load from file
    json_data = json.loads(sk_data)

    inference_client = InferenceClient.construct_from_credentials(
        dar_url=json_data['url'],
        clientid=json_data['uaa']['clientid'],
        clientsecret=json_data['uaa']['clientsecret'],
        uaa_url=json_data['uaa']['url'],
    )

    # The code passes two objects to be classified. Each object
    # must have all features described in the DatasetSchema used
    # during training.
    objects_to_be_classified = [
        {
            "objectId": "optional-identifier-1",
            "features": [
                {"name": "manufacturer", "value": "Energizer"},
                {"name": "description", "value": "Alkaline batteries; 1.5V"},
                {"name": "price", "value":  "5.99"},
            ],
        },
        {
            "objectId": "optional-identifier-2",
            "features": [
                {"name": "manufacturer", "value": "Eidos"},
                {"name": "description", "value": "Unravel a grim conspiracy at the brink of Revolution"},
                {"name": "price", "value":  "19.99"},
            ],
        },
    ]

    inference_response = inference_client.create_inference_request(
        model_name=MODEL_NAME,
        objects=objects_to_be_classified
    )

    pprint.pprint(inference_response)

The script will print the API response obtained from the RESTful API:

.. code-block:: python

    {
        'id': '09ade1bd-1da0-4060-45bd-185b31afba24',
        'processedTime': '2020-07-03T15:22:28.124490+00:00',
        'status': 'DONE',
        'predictions': [
            {
                'labels': [
                    {
                        'name': 'level1_category',
                        'results': [{
                            'probability': 1.0,
                            'value': 'Connected Home & '
                                     'Housewares'
                        }]
                    },
                    {
                        'name': 'level2_category',
                        'results': [{
                            'probability': 0.99999976,
                            'value': 'Housewares'
                        }]
                    },
                    {
                        'name': 'level3_category',
                        'results': [{
                            'probability': 0.9999862,
                             'value': 'Household Batteries'
                        }]
                    }
                ],
                'objectId': 'optional-identifier-1'
            },
            {
                'labels': [
                    {
                        'name': 'level1_category',
                        'results': [{
                            'probability': 0.99775535,
                            'value': 'Video Games'
                        }]
                    },
                    {
                        'name': 'level2_category',
                        'results': [{
                            'probability': 0.5394639,
                            'value': 'PlayStation 3'
                        }]
                    },
                    {
                        'name': 'level3_category',
                        'results': [{
                            'probability': 0.40110978,
                            'value': 'PS3 Games'
                        }]
                    }
                ],
                'objectId': 'optional-identifier-2'
            }
        ]
    }

For each of the two objects sent to the inference endpoint, all three labels specified
in the DatasetSchema are returned. Feel free to try this with your own input!

.. note::

    To see more than one prediction per label, pass the **top_n** parameter to the
    :meth:`~sap.aibus.dar.client.inference_client.InferenceClient.create_inference_request`
    method. This will then also return the n-best (second-best...) predictions.

.. note::

    To predict more than fifty objects at a time, consider the
    :meth:`~sap.aibus.dar.client.inference_client.InferenceClient.do_bulk_inference` method.
    This is especially useful for batch-processing, e.g. of CSV files.

SDK API Documentation
*********************

See :ref:`api`.

Security Guide
**************

See :ref:`security guide`.

Improving Resilience
********************

See :ref:`retry`.

Table of Contents
=================
..  toctree::
    :maxdepth: 2
    :caption: Contents:

    Introduction <self>
    api.rst
    retry.rst
    security.rst
    development.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
