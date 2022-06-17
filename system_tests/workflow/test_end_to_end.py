import logging
import uuid
from io import BytesIO
import os

import pytest

from sap.aibus.dar.client.inference_constants import InferencePaths
from sap.aibus.dar.client.data_manager_client import DataManagerClient
from sap.aibus.dar.client.exceptions import DARHTTPException, ModelAlreadyExists
from sap.aibus.dar.client.inference_client import InferenceClient
from sap.aibus.dar.client.model_manager_client import ModelManagerClient
from sap.aibus.dar.client.workflow.model import ModelCreator

logger = logging.getLogger("test")


@pytest.mark.requirements(issues=["42", "60"])
class TestEndToEnd:
    """
    Tests an end-to-end scenario:

    * training
    * deployment
    * inference (TBD)
    """

    def test_create(
        self,
        model_creator: ModelCreator,
        model_manager_client: ModelManagerClient,
        data_manager_client: DataManagerClient,
        inference_client: InferenceClient,
    ):
        """
        :param model_creator: provided by pytest fixture, see conftest.py
        :param model_manager_client: provided by pytest fixture, see conftest.py
        :param data_manager_client: provided by pytest fixture, see conftest.py
        """
        # When running under pytest, logging will not be emitted to stdout
        # by pytest by default.
        ModelCreator.setup_basic_logging(debug=False)

        csv = """
        manufacturer,description,category,subcategory
        me,"simple è test, records",A,AA
        me,"übrigens ein Beispiel, records",A,AA
        me,"un po' di testo",A,AA
        me,"какой-то текст",A,AA
        me,"du texte",A,AA
        me,"一些文字",A,AA
        me,"कुछ पाठ",A,AA
        me,"κάποιο κείμενο",A,AA
        me,"кейбір мәтін",A,AA
        me,"iu teksto",A,AA
        """

        data_stream = BytesIO(csv.strip().encode("utf-8"))

        new_schema = {
            "features": [
                {"label": "manufacturer", "type": "CATEGORY"},
                {"label": "description", "type": "TEXT"},
            ],
            "labels": [
                {"label": "category", "type": "CATEGORY"},
                {"label": "subcategory", "type": "CATEGORY"},
            ],
            "name": "test",
        }

        model_name = "dar-client-test-" + str(uuid.uuid4())

        # Before we start: model is not there
        with pytest.raises(DARHTTPException) as exc_info:
            model_manager_client.read_model_by_name(model_name)

        assert exc_info.value.status_code == 404

        # Create model
        resp = model_creator.create(
            model_template_id="d7810207-ca31-4d4d-9b5a-841a644fd81f",
            dataset_schema=new_schema,
            model_name=model_name,
            data_stream=data_stream,
        )

        assert resp["name"] == model_name
        assert "validationResult" in resp

        # Now that the model exists, a second, identical call should
        # raise a ModelAlreadyExists exception.

        with pytest.raises(ModelAlreadyExists):
            model_creator.create(
                model_template_id="d7810207-ca31-4d4d-9b5a-841a644fd81f",
                dataset_schema=new_schema,
                model_name=model_name,
                data_stream=data_stream,
            )

        # Check if model is indeed there
        self._assert_model_exists(model_manager_client, model_name)

        # Attempt to deploy model
        deployment_resource = model_manager_client.deploy_and_wait(model_name)
        deployment_id = deployment_resource["id"]
        logger.info(
            "Deployed model '%s' with deployment ID '%s'", model_name, deployment_id
        )

        self._assert_deployment_exists(deployment_id, model_manager_client)

        # Test inference
        self._assert_inference_works(inference_client, model_name)

        # Now delete deployment by model name (i.e. undeploy model)
        model_manager_client.ensure_model_is_undeployed(model_name)

        # Deployment should be gone
        self._assert_deployment_does_not_exist(model_manager_client, deployment_id)

        # Deploy model again, to exercise ensure_deployment_exists
        deployment_resource = model_manager_client.ensure_deployment_exists(model_name)
        deployment_id = deployment_resource["id"]
        model_manager_client.wait_for_deployment(deployment_id)

        self._assert_deployment_exists(deployment_id, model_manager_client)
        # Now delete deployment (i.e. undeploy model)
        model_manager_client.delete_deployment_by_id(deployment_id)

        # Deployment should be gone
        self._assert_deployment_does_not_exist(model_manager_client, deployment_id)

        # Delete Model
        model_manager_client.delete_model_by_name(model_name)
        # Model should now be gone
        self._assert_model_does_not_exist(model_manager_client, model_name)

        # Now check resources created internally by ModelCreator.create
        # and clean up!

        # Job
        # The Model resource does not have a jobId property, so we
        # have to look up the job ID via the job collection
        job = model_manager_client.read_job_by_model_name(model_name)
        assert job["id"] is not None
        job_id = job["id"]

        self._assert_job_exists(model_manager_client, job_id)
        # Get dataset ID used in this job
        job_resource = model_manager_client.read_job_by_id(job_id)
        dataset_id = job_resource["datasetId"]
        # Clean up job
        model_manager_client.delete_job_by_id(job_id)
        self._assert_job_does_not_exist(model_manager_client, job_id)

        # Dataset
        self._assert_dataset_exists(data_manager_client, dataset_id)
        # Get DatasetSchema used in this Dataset
        dataset_resource = data_manager_client.read_dataset_by_id(dataset_id)
        dataset_schema_id = dataset_resource["datasetSchemaId"]
        # Clean up Dataset
        data_manager_client.delete_dataset_by_id(dataset_id)
        self._assert_dataset_does_not_exist(data_manager_client, dataset_id)

        # DatasetSchema
        self._assert_dataset_schema_exists(data_manager_client, dataset_schema_id)
        # Clean up DatasetSchema
        data_manager_client.delete_dataset_schema_by_id(dataset_schema_id)
        self._assert_dataset_schema_does_not_exist(
            data_manager_client, dataset_schema_id
        )

    def _assert_dataset_schema_exists(self, data_manager_client, dataset_schema_id):
        read_response = data_manager_client.read_dataset_schema_by_id(dataset_schema_id)
        assert read_response["id"] == dataset_schema_id
        # And check collection
        dataset_schema_collection = data_manager_client.read_dataset_schema_collection()
        dataset_schema_ids = [
            item["id"] for item in dataset_schema_collection["datasetSchemas"]
        ]
        assert dataset_schema_id in dataset_schema_ids

    def _assert_dataset_exists(self, data_manager_client, dataset_id):
        read_response = data_manager_client.read_dataset_by_id(dataset_id)
        assert read_response["id"] == dataset_id
        # And check collection
        dataset_collection = data_manager_client.read_dataset_collection()
        dataset_ids = [item["id"] for item in dataset_collection["datasets"]]
        assert dataset_id in dataset_ids

    def _assert_job_exists(self, model_manager_client, job_id):
        read_response = model_manager_client.read_job_by_id(job_id)
        assert read_response["id"] == job_id
        # And check collection
        job_collection = model_manager_client.read_job_collection()
        job_ids = [item["id"] for item in job_collection["jobs"]]
        assert job_id in job_ids

    def _assert_dataset_schema_does_not_exist(
        self, data_manager_client, dataset_schema_id
    ):
        with pytest.raises(DARHTTPException) as exc_info:
            data_manager_client.read_dataset_schema_by_id(dataset_schema_id)
        assert exc_info.value.status_code == 404
        # Check that Model is gone from resource as well
        dataset_schema_collection = data_manager_client.read_dataset_schema_collection()
        observed_dataset_schema_ids = [
            resource["id"] for resource in dataset_schema_collection["datasetSchemas"]
        ]
        assert dataset_schema_id not in observed_dataset_schema_ids

    def _assert_dataset_does_not_exist(self, data_manager_client, dataset_id):
        with pytest.raises(DARHTTPException) as exc_info:
            data_manager_client.read_dataset_by_id(dataset_id)
        assert exc_info.value.status_code == 404
        # Check that Model is gone from resource as well
        dataset_collection = data_manager_client.read_dataset_collection()
        observed_dataset_ids = [
            resource["id"] for resource in dataset_collection["datasets"]
        ]
        assert dataset_id not in observed_dataset_ids

    def _assert_job_does_not_exist(self, model_manager_client, job_id):
        with pytest.raises(DARHTTPException) as exc_info:
            model_manager_client.read_job_by_id(job_id)
        assert exc_info.value.status_code == 404
        # Check that Model is gone from resource as well
        job_collection = model_manager_client.read_job_collection()
        observed_job_ids = [resource["id"] for resource in job_collection["jobs"]]
        assert job_id not in observed_job_ids

    def _assert_inference_works(self, inference_client, model_name):
        to_be_classified = [
            {
                "objectId": "b5cbcb34-7ab9-4da5-b7ec-654c90757eb9",
                "features": [
                    {"name": "manufacturer", "value": "me"},
                    {"name": "description", "value": "übrigens ein Beispiel, records"},
                ],
            }
        ]
        response = inference_client.create_inference_request(
            model_name=model_name, objects=to_be_classified
        )
        logger.info("Inference done. API response: %s", response)
        print(response)
        # One object has been classified
        assert len(response["predictions"]) == 1

        # do_bulk_inference with concurrency
        big_to_be_classified = [to_be_classified[0] for _ in range(123)]
        response = inference_client.do_bulk_inference(
            model_name=model_name, objects=big_to_be_classified
        )
        assert len(response) == 123

        # do_bulk_inference without concurrency
        response = inference_client.do_bulk_inference(
            model_name=model_name, objects=big_to_be_classified, worker_count=1
        )
        assert len(response) == 123

        url = os.environ["DAR_URL"]
        if url[-1] == "/":
            url = url[:-1]
        url = url + InferencePaths.format_inference_endpoint_by_name(model_name)
        response = inference_client.create_inference_request_with_url(
            url=url, objects=to_be_classified
        )
        logger.info("Inference with URL done. API response: %s", response)
        print(response)
        # One object has been classified
        assert len(response["predictions"]) == 1

    def _assert_deployment_exists(self, deployment_id, model_manager_client):
        # Look at individual resource
        read_response = model_manager_client.read_deployment_by_id(deployment_id)
        assert read_response["id"] == deployment_id
        # And check collection
        deployment_collections = model_manager_client.read_deployment_collection()
        deployment_ids = [item["id"] for item in deployment_collections["deployments"]]
        assert deployment_id in deployment_ids

    def _assert_model_exists(self, model_manager_client, model_name):
        # Look at individual Model resource
        model_resource = model_manager_client.read_model_by_name(model_name)
        assert model_resource["name"] == model_name
        # Also check model collection
        model_collection = model_manager_client.read_model_collection()
        observed_model_names = [
            resource["name"] for resource in model_collection["models"]
        ]
        assert model_name in observed_model_names

    def _assert_model_does_not_exist(self, model_manager_client, model_name):
        # Check that individual model resource does not exist
        with pytest.raises(DARHTTPException) as exc_info:
            model_manager_client.read_model_by_name(model_name)
        assert exc_info.value.status_code == 404
        # Check that Model is gone from resource as well
        model_collection = model_manager_client.read_model_collection()
        observed_model_names = [
            resource["name"] for resource in model_collection["models"]
        ]
        assert model_name not in observed_model_names

    def _assert_deployment_does_not_exist(self, model_manager_client, deployment_id):
        # Check that individual deployment does not exist
        with pytest.raises(DARHTTPException) as exc_info:
            model_manager_client.read_deployment_by_id(deployment_id)
        assert exc_info.value.status_code == 404
        # Check that deployment is gone from collection
        deployment_collections = model_manager_client.read_deployment_collection()
        deployment_ids = [item["id"] for item in deployment_collections["deployments"]]
        assert deployment_id not in deployment_ids
