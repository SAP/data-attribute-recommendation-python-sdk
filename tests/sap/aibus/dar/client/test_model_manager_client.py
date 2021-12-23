# type: ignore[assignment]
# The pragma above causes mypy to ignore this file:
# mypy cannot deal with some of the monkey-patching we do below.
# https://github.com/python/mypy/issues/2427
import uuid
from unittest.mock import call, create_autospec, patch

import pytest

from sap.aibus.dar.client.exceptions import (
    TrainingJobFailed,
    TrainingJobTimeOut,
    DeploymentTimeOut,
    DeploymentFailed,
    CreateTrainingJobFailed,
    JobNotFound,
)
from sap.aibus.dar.client.model_manager_client import ModelManagerClient
from sap.aibus.dar.client.util.polling import Polling, PollingTimeoutException
from tests.sap.aibus.dar.client.test_data_manager_client import (
    AbstractDARClientConstruction,
    prepare_client,
)


class TestModelManagerClientConstruction(AbstractDARClientConstruction):
    clazz = ModelManagerClient


DAR_URL = "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/"


@pytest.fixture()
def model_manager_client():
    return prepare_client(DAR_URL, ModelManagerClient)


def make_deployment_resource(status=None, random_data=False):
    deployment_resource = {
        "id": "51125156-c039-460c-9c02-2e3fc0c89da1",
        "deployedAt": "2020-02-24T08:49:04+00:00",
        "modelName": "test-model",
    }
    if status is not None:
        deployment_resource["status"] = status
    if random_data:
        deployment_resource["id"] = str(uuid.uuid4())
        deployment_resource["modelName"] = "model-" + deployment_resource["id"]
    return deployment_resource


def assert_get_response_is_json(client, response):
    """
    Assert that the response is the JSON returned by session.get_from_endpoint.

    Of course, this is all mock objects, so this checks if the mock objects are
    identical and if the methods were called correctly.
    """
    assert client.session.get_from_endpoint.return_value.json.return_value == response


def assert_get_from_endpoint_called_with_endpoint(client, expected_endpoint):
    assert client.session.get_from_endpoint.call_args_list == [call(expected_endpoint)]


class TestModelManagerClientModelTemplate:
    def test_read_model_template_collection(self, model_manager_client):
        response = model_manager_client.read_model_template_collection()
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/modelTemplates"
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )

    def test_read_model_template_by_id(self, model_manager_client):
        model_template_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"

        response = model_manager_client.read_model_template_by_id(
            "d7810207-ca31-4d4d-9b5a-841a644fd81f"
        )
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/modelTemplates/{}".format(
            model_template_id
        )
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )


class TestModelManagerClientModelJob:
    def test_read_job_collection(self, model_manager_client):
        response = model_manager_client.read_job_collection()
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/jobs"
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )

    def test_read_job_by_id(self, model_manager_client):
        job_id = "bf10eede-2f7b-49f3-815f-eccc04fc9e56"

        response = model_manager_client.read_job_by_id(job_id)
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/jobs/{}".format(job_id)
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )

    def test_delete_job_by_id(self, model_manager_client):
        job_id = "bf10eede-2f7b-49f3-815f-eccc04fc9e56"
        response = model_manager_client.delete_job_by_id(job_id)
        assert response is None

        expected_endpoint = "/model-manager/api/v3/jobs/{}".format(job_id)
        assert model_manager_client.session.delete_from_endpoint.call_args_list == [
            call(expected_endpoint)
        ]

    def test_create_job(self, model_manager_client):
        model_template_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"
        dataset_id = "a2058037-2ae4-465e-8110-65381d47f3d4"
        model_name = "my_test_model"

        model_manager_client.session.post_to_endpoint.return_value.json.return_value = {
            "id": "abcd"
        }

        response = model_manager_client.create_job(
            model_template_id=model_template_id,
            dataset_id=dataset_id,
            model_name=model_name,
        )

        expected_url = "/model-manager/api/v3/jobs"
        expected_payload = {
            "datasetId": dataset_id,
            "modelTemplateId": model_template_id,
            "modelName": model_name,
        }

        expected_post_call = [call(expected_url, payload=expected_payload)]

        assert (
            expected_post_call
            == model_manager_client.session.post_to_endpoint.call_args_list
        )

        assert (
            model_manager_client.session.post_to_endpoint.return_value.json.return_value
            == response
        )

    def test_create_job_with_business_blueprint_id(self, model_manager_client):
        """
        Tests start_job correctly with business_blueprint_id
        """
        business_blueprint_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"
        dataset_id = "a2058037-2ae4-465e-8110-65381d47f3d4"
        model_name = "my_test_model"

        model_manager_client.session.post_to_endpoint.return_value.json.return_value = {
            "id": "abcd"
        }

        response = model_manager_client.create_job(
            model_template_id=None,
            business_blueprint_id=business_blueprint_id,
            dataset_id=dataset_id,
            model_name=model_name,
        )

        expected_url = "/model-manager/api/v3/jobs"
        expected_payload = {
            "datasetId": dataset_id,
            "businessBlueprintId": business_blueprint_id,
            "modelName": model_name,
        }

        expected_post_call = [call(expected_url, payload=expected_payload)]

        assert (
            expected_post_call
            == model_manager_client.session.post_to_endpoint.call_args_list
        )

        assert (
            model_manager_client.session.post_to_endpoint.return_value.json.return_value
            == response
        )

    def test_create_job_with_business_blueprint_id_and_model_template_id(
        self, model_manager_client
    ):
        """
        Tests it throws the exception if both model_template_id
        and model_template_id is provided
        """
        business_blueprint_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"
        model_template_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"
        dataset_id = "a2058037-2ae4-465e-8110-65381d47f3d4"
        model_name = "my_test_model"

        with pytest.raises(CreateTrainingJobFailed) as exception:
            model_manager_client.create_job(
                model_template_id=model_template_id,
                business_blueprint_id=business_blueprint_id,
                dataset_id=dataset_id,
                model_name=model_name,
            )
        expected_message = (
            "Either model_template_id or business_blueprint_id"
            " have to be specified, not both."
        )
        assert str(exception.value) == expected_message

    def test_create_job_without_business_blueprint_id_and_model_template_id(
        self, model_manager_client
    ):
        """
        Tests it throws the exception if both model_template_id and
        model_template_id is provided
        """
        dataset_id = "a2058037-2ae4-465e-8110-65381d47f3d4"
        model_name = "my_test_model"

        with pytest.raises(CreateTrainingJobFailed) as exception:
            model_manager_client.create_job(
                model_template_id=None,
                business_blueprint_id=None,
                dataset_id=dataset_id,
                model_name=model_name,
            )
        expected_message = (
            "Either model_template_id or business_blueprint_id have to be specified."
        )
        assert str(exception.value) == expected_message

    def test_create_job_with_empty_business_blueprint_id_and_model_template_id(
        self, model_manager_client
    ):
        """
        Tests it throws the exception if both model_template_id and
        model_template_id is provided
        """
        dataset_id = "a2058037-2ae4-465e-8110-65381d47f3d4"
        model_name = "my_test_model"

        with pytest.raises(CreateTrainingJobFailed) as exception:
            model_manager_client.create_job(
                model_template_id="",
                business_blueprint_id="",
                dataset_id=dataset_id,
                model_name=model_name,
            )
        expected_message = (
            "Either model_template_id or business_blueprint_id have to be specified."
        )
        assert str(exception.value) == expected_message

    def test_wait_for_job_uses_polling(self, model_manager_client: ModelManagerClient):
        """
        Tests the interaction of the `wait_for_job` method with the Polling class.
        """

        # type: ignore
        polling_mock_clazz = create_autospec(Polling)

        polling_mock = polling_mock_clazz.return_value

        model_manager_client.polling_class = lambda: polling_mock_clazz

        model_manager_client.read_job_by_id = create_autospec(
            model_manager_client.read_job_by_id
        )
        model_manager_client.is_job_failed = create_autospec(
            model_manager_client.is_job_failed, return_value=False
        )

        job_id = "ac0429b7-fb21-466b-b134-7c4643d35bec"

        # Act
        return_value = model_manager_client.wait_for_job(job_id)

        # Assert
        assert return_value == polling_mock.poll_until_success.return_value

        expected_polling_constructor_args = call(
            timeout_seconds=24 * 60 * 60, intervall_seconds=60
        )
        assert polling_mock_clazz.call_args_list == [expected_polling_constructor_args]

        assert polling_mock.poll_until_success.call_count == 1
        kwargs = polling_mock.poll_until_success.call_args[1]
        given_polling_function = kwargs["polling_function"]
        # Given that we mock the Polling class, so far nothing
        # should have called the read_job_by_id function
        assert model_manager_client.read_job_by_id.call_count == 0
        # Now, when we call the polling_function manually, it should
        # call model_manager_client.read_job_by_id
        given_polling_function()
        assert model_manager_client.read_job_by_id.call_args_list == [call(job_id)]

        given_success_function = kwargs["success_function"]
        assert given_success_function == model_manager_client.is_job_finished

    def test_wait_for_job_raises_if_job_is_failed(
        self, model_manager_client: ModelManagerClient
    ):
        """
        Tests that correct exception is raised by wait_for_job()
        if job finishes with status FAILED.
        """

        model_manager_client.read_job_by_id = create_autospec(
            model_manager_client.read_job_by_id,
            return_value=self._make_job_resource("FAILED"),
        )

        job_id = "61b6f2ea-cf1c-4ba0-825a-1185671c517b"
        with pytest.raises(TrainingJobFailed) as exc_info:
            model_manager_client.wait_for_job(job_id)

        expected_message = "Job '{}' has status: 'FAILED'".format(job_id)
        assert str(exc_info.value) == expected_message

    def test_wait_for_job_raises_if_job_times_out(
        self, model_manager_client: ModelManagerClient
    ):
        """
        Tests that correct exception is raised by wait_for_job() if job polling times
        out.
        """
        polling_mock_clazz = create_autospec(Polling)

        polling_mock = polling_mock_clazz.return_value

        model_manager_client.polling_class = lambda: polling_mock_clazz

        polling_mock.poll_until_success.side_effect = PollingTimeoutException

        job_id = "61b6f2ea-cf1c-4ba0-825a-1185671c517b"
        with pytest.raises(TrainingJobTimeOut) as exc_info:
            model_manager_client.wait_for_job(job_id)

        expected_message = "Training job '{}' did not finish within {}s".format(
            job_id, 24 * 60 * 60
        )

        assert str(exc_info.value) == expected_message

    def test_create_job_and_wait(self, model_manager_client: ModelManagerClient):
        """
        Tests if start_job_and_wait correctly orchestrates start_job()
        and wait_for_job().
        """
        model_template_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"
        dataset_id = "a2058037-2ae4-465e-8110-65381d47f3d4"
        model_name = "my_test_model"

        job_resource = self._make_job_resource("SUCCEEDED")

        model_manager_client.create_job = create_autospec(
            model_manager_client.create_job
        )
        model_manager_client.create_job.return_value = job_resource

        model_manager_client.wait_for_job = create_autospec(
            model_manager_client.wait_for_job
        )

        ret_val = model_manager_client.create_job_and_wait(
            model_name=model_name,
            dataset_id=dataset_id,
            model_template_id=model_template_id,
        )

        assert ret_val == model_manager_client.wait_for_job.return_value

        expected_create_job_call_args = call(
            model_template_id=model_template_id,
            dataset_id=dataset_id,
            model_name=model_name,
            business_blueprint_id=None,
        )

        assert model_manager_client.create_job.call_args_list == [
            expected_create_job_call_args
        ]

        expected_wait_for_job_call_args = call(job_resource["id"])

        assert model_manager_client.wait_for_job.call_args_list == [
            expected_wait_for_job_call_args
        ]

    def test_create_job_and_wait_with_business_blueprint_id(
        self, model_manager_client: ModelManagerClient
    ):
        """
        Tests if start_job_and_wait correctly with business_blueprint_id
        orchestrates start_job() and wait_for_job().
        """
        business_blueprint_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"
        dataset_id = "a2058037-2ae4-465e-8110-65381d47f3d4"
        model_name = "my_test_model"

        job_resource = self._make_job_resource("SUCCEEDED")

        model_manager_client.create_job = create_autospec(
            model_manager_client.create_job
        )
        model_manager_client.create_job.return_value = job_resource

        model_manager_client.wait_for_job = create_autospec(
            model_manager_client.wait_for_job
        )

        ret_val = model_manager_client.create_job_and_wait(
            model_name=model_name,
            dataset_id=dataset_id,
            model_template_id="",
            business_blueprint_id=business_blueprint_id,
        )

        assert ret_val == model_manager_client.wait_for_job.return_value

        expected_create_job_call_args = call(
            model_template_id="",
            dataset_id=dataset_id,
            model_name=model_name,
            business_blueprint_id=business_blueprint_id,
        )

        assert model_manager_client.create_job.call_args_list == [
            expected_create_job_call_args
        ]

        expected_wait_for_job_call_args = call(job_resource["id"])

        assert model_manager_client.wait_for_job.call_args_list == [
            expected_wait_for_job_call_args
        ]

    def test_is_job_finished(self):

        final_states = ["SUCCEEDED", "FAILED"]
        for final_state in final_states:
            res = self._make_job_resource(final_state)
            assert ModelManagerClient.is_job_finished(res) is True

        non_final_states = ["PENDING", "RUNNING"]

        for non_final_state in non_final_states:
            res = self._make_job_resource(non_final_state)
            assert ModelManagerClient.is_job_finished(res) is False

    def test_is_job_failed(self):
        non_failed_states = ["SUCCEEDED", "PENDING", "RUNNING"]

        failed_job = self._make_job_resource("FAILED")
        assert ModelManagerClient.is_job_failed(failed_job) is True

        for non_failed_state in non_failed_states:
            non_failed_job = self._make_job_resource(non_failed_state)
            assert ModelManagerClient.is_job_failed(non_failed_job) is False

    def test_read_job_by_model_name(self, model_manager_client: ModelManagerClient):
        job1 = self._make_job_resource("SUCCEEDED")
        job2 = self._make_job_resource("SUCCEEDED")
        job2["modelName"] = "my-model-2"
        job_collection_response = {"count": 2, "jobs": [job1, job2]}
        model_manager_client.read_job_collection = create_autospec(
            model_manager_client.read_job_collection,
            return_value=job_collection_response,
        )
        response = model_manager_client.read_job_by_model_name("my-model-1")
        assert response["modelName"] == "my-model-1"
        assert model_manager_client.read_job_collection.call_count == 1

    def test_read_job_by_model_name_job_not_found(
        self, model_manager_client: ModelManagerClient
    ):
        job1 = self._make_job_resource("SUCCEEDED")
        job2 = self._make_job_resource("SUCCEEDED")
        job2["modelName"] = "my-model-2"
        job_collection_response = {"count": 2, "jobs": [job1, job2]}
        model_manager_client.read_job_collection = create_autospec(
            model_manager_client.read_job_collection,
            return_value=job_collection_response,
        )
        with pytest.raises(JobNotFound) as exc:
            model_manager_client.read_job_by_model_name("my-model-3")
        expected_message = "Job with model name 'my-model-3' could not be found"
        assert str(exc.value) == expected_message
        assert model_manager_client.read_job_collection.call_count == 1

    @staticmethod
    def _make_job_resource(state):
        job_resource = {
            "datasetId": "873d9d7c-c7d6-49da-9a0c-850692d36df7",
            "endedAt": None,
            "id": "512c7299-d31d-41e7-bf1c-674ff87f3bea",
            "maxTrainingTime": None,
            "message": None,
            "modelName": "my-model-1",
            "modelTemplateId": "d7810207-ca31-4d4d-9b5a-841a644fd81f",
            "progress": 0,
            "startedAt": None,
            "status": state,
            "submittedAt": "2020-03-03T10:48:12+00:00",
        }
        return job_resource


class TestModelManagerClientModel:
    def test_read_model_collection(self, model_manager_client):
        response = model_manager_client.read_model_collection()
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/models"
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )

    def test_read_model_by_name(self, model_manager_client):
        response = model_manager_client.read_model_by_name("my-model")
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/models/my-model"
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )

    def test_delete_model_by_name(self, model_manager_client):
        model_name = "to-be-deleted"
        response = model_manager_client.delete_model_by_name(model_name)
        assert response is None

        expected_endpoint = "/model-manager/api/v3/models/{}".format(model_name)
        assert model_manager_client.session.delete_from_endpoint.call_args_list == [
            call(expected_endpoint)
        ]


class TestModelManagerClientDeployment:
    def test_read_deployment_collection(self, model_manager_client: ModelManagerClient):
        response = model_manager_client.read_deployment_collection()
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/deployments"
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )

    def test_read_deployment_by_id(self, model_manager_client: ModelManagerClient):
        deployment_id = "b8285a61-d711-4d36-9c25-2da80929f734"
        response = model_manager_client.read_deployment_by_id(deployment_id)
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/deployments/" + deployment_id
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )

    def test_delete_deployment_by_id(self, model_manager_client: ModelManagerClient):
        deployment_id = "a523baec-0174-4d2d-89a3-2782ddf805bb"
        response = model_manager_client.delete_deployment_by_id(deployment_id)
        assert response is None

        expected_endpoint = "/model-manager/api/v3/deployments/{}".format(deployment_id)
        assert model_manager_client.session.delete_from_endpoint.call_args_list == [
            call(expected_endpoint)
        ]

    def test_ensure_model_is_undeployed(self, model_manager_client: ModelManagerClient):
        """
        Tests ModelManagerClient.ensure_model_is_undeployed for the case where the model
        is deployed and must be undeployed.
        """

        # prepare
        deployment_id = "a1ce6326-7356-4504-875e-da1d10c90ea0"

        model_manager_client.lookup_deployment_id_by_model_name = create_autospec(
            model_manager_client.lookup_deployment_id_by_model_name,
            return_value=deployment_id,
        )

        model_manager_client.delete_deployment_by_id = create_autospec(
            model_manager_client.delete_deployment_by_id
        )

        # Act
        result = model_manager_client.ensure_model_is_undeployed("test-model")

        # Assert

        assert result == deployment_id

        expected_lookup_call = call("test-model")
        assert (
            model_manager_client.lookup_deployment_id_by_model_name.call_args_list
            == [expected_lookup_call]
        )

        expected_delete_call = call(deployment_id)
        assert model_manager_client.delete_deployment_by_id.call_args_list == [
            expected_delete_call
        ]

    def test_ensure_model_is_undeployed_already_undeployed(
        self, model_manager_client: ModelManagerClient
    ):

        """
        Tests ModelManagerClient.ensure_model_is_undeployed for the case where the model
        is not deployed. In this case, there is nothing to undeploy.
        """
        # prepare
        model_manager_client.lookup_deployment_id_by_model_name = create_autospec(
            model_manager_client.lookup_deployment_id_by_model_name, return_value=None
        )

        model_manager_client.delete_deployment_by_id = create_autospec(
            model_manager_client.delete_deployment_by_id
        )

        # Act
        result = model_manager_client.ensure_model_is_undeployed("test-model")

        # Assert
        assert result is None

        expected_lookup_call = call("test-model")
        assert (
            model_manager_client.lookup_deployment_id_by_model_name.call_args_list
            == [expected_lookup_call]
        )

        assert model_manager_client.delete_deployment_by_id.call_count == 0

    def test_create_deployment(self, model_manager_client: ModelManagerClient):
        model_name = "my_test_model"

        response = model_manager_client.create_deployment(model_name=model_name)

        expected_url = "/model-manager/api/v3/deployments"
        expected_payload = {"modelName": model_name}

        expected_post_call = [call(expected_url, payload=expected_payload)]

        assert (
            expected_post_call
            == model_manager_client.session.post_to_endpoint.call_args_list
        )

        assert (
            model_manager_client.session.post_to_endpoint.return_value.json.return_value
            == response
        )

    def _make_deployment_resource(self, status):
        return make_deployment_resource(status)

    def test_is_deployment_finished(self):

        final_states = ["SUCCEEDED", "STOPPED", "FAILED"]

        non_final_states = ["PENDING"]

        for final_state in final_states:
            resource = self._make_deployment_resource(final_state)

            assert ModelManagerClient.is_deployment_finished(resource) is True

        for non_final_state in non_final_states:
            resource = self._make_deployment_resource(non_final_state)
            assert ModelManagerClient.is_deployment_finished(resource) is False

    def test_is_deployment_failed(self):

        ok_states = ["SUCCEEDED", "PENDING"]
        failed_states = ["STOPPED", "FAILED"]

        for ok_state in ok_states:
            resource = self._make_deployment_resource(ok_state)
            assert ModelManagerClient.is_deployment_failed(resource) is False

        for failed_state in failed_states:
            resource = self._make_deployment_resource(failed_state)
            assert ModelManagerClient.is_deployment_failed(resource) is True

    def test_wait_for_deployment_uses_polling(
        self, model_manager_client: ModelManagerClient
    ):
        """
        Tests the interaction of the `wait_for_polling` method with the
        Polling class.
        """
        # type: ignore
        polling_mock_clazz = create_autospec(Polling)

        polling_mock = polling_mock_clazz.return_value

        model_manager_client.polling_class = lambda: polling_mock_clazz

        model_manager_client.read_deployment_by_id = create_autospec(
            model_manager_client.read_deployment_by_id
        )
        model_manager_client.is_deployment_failed = create_autospec(
            model_manager_client.is_deployment_failed, return_value=False
        )

        deployment_id = "7d36e2c7-aaa4-4003-a3e4-a4e7b94328e7"

        # Act
        return_value = model_manager_client.wait_for_deployment(deployment_id)
        # TODO: should raise if deployment is already failed initially

        # Assert
        assert return_value == polling_mock.poll_until_success.return_value

        expected_polling_constructor_args = call(
            timeout_seconds=30 * 60, intervall_seconds=45
        )
        assert polling_mock_clazz.call_args_list == [expected_polling_constructor_args]

        assert polling_mock.poll_until_success.call_count == 1
        kwargs = polling_mock.poll_until_success.call_args[1]
        given_polling_function = kwargs["polling_function"]
        # Given that we mock the Polling class, so far nothing
        # should have called the read_job_by_id function
        assert model_manager_client.read_deployment_by_id.call_count == 0
        # Now, when we call the polling_function manually, it should
        # call model_manager_client.read_job_by_id
        given_polling_function()
        assert model_manager_client.read_deployment_by_id.call_args_list == [
            call(deployment_id)
        ]

        given_success_function = kwargs["success_function"]
        assert given_success_function == model_manager_client.is_deployment_finished

    def test_wait_for_deployment_raises_on_timeout(
        self, model_manager_client: ModelManagerClient
    ):
        """
        If polling raises a PollingTimeoutException, the *wait_for_deployment*
        method should re-raise as a DeploymentTimeOut.

        """
        # type: ignore
        polling_mock_clazz = create_autospec(Polling)

        polling_mock = polling_mock_clazz.return_value

        model_manager_client.polling_class = lambda: polling_mock_clazz

        polling_mock.poll_until_success.side_effect = PollingTimeoutException

        deployment_id = "7d36e2c7-aaa4-4003-a3e4-a4e7b94328e7"

        with pytest.raises(DeploymentTimeOut) as exc_info:
            model_manager_client.wait_for_deployment(deployment_id)

        expected_message = "Deployment '{}' did not succeed within {}s".format(
            deployment_id, 30 * 60
        )

        assert str(exc_info.value) == expected_message

    def test_wait_for_deployment_raises_on_failed_deployment(
        self, model_manager_client: ModelManagerClient
    ):
        """
        If the Deployment finishes, but is failed, then *wait_for_deployment* should
        raise DeploymentFailed.
        """

        model_manager_client.read_deployment_by_id = create_autospec(
            model_manager_client.read_deployment_by_id,
            return_value=self._make_deployment_resource("FAILED"),
        )

        deployment_id = "7d36e2c7-aaa4-4003-a3e4-a4e7b94328e7"

        with pytest.raises(DeploymentFailed) as exc_info:
            model_manager_client.wait_for_deployment(deployment_id)

        expected_msg = "Deployment '{}' has status: FAILED".format(deployment_id)

        assert expected_msg == str(exc_info.value)

    def test_deploy_and_wait(self, model_manager_client: ModelManagerClient):
        """
        Tests if *deploy_and_wait* orchestrates *create_deployment* and
        *wait_for_deployment* correctly.
        """

        # prepare
        deployment_resource = self._make_deployment_resource("PENDING")
        model_manager_client.create_deployment = create_autospec(
            model_manager_client.create_deployment, return_value=deployment_resource
        )

        model_manager_client.wait_for_deployment = create_autospec(
            model_manager_client.wait_for_deployment
        )

        # act
        model_name = "my-test-model"
        return_value = model_manager_client.deploy_and_wait(model_name=model_name)

        # assert
        assert return_value == model_manager_client.wait_for_deployment.return_value

        expected_call_to_create_deployment = call(model_name=model_name)

        assert model_manager_client.create_deployment.call_args_list == [
            expected_call_to_create_deployment
        ]

        expected_call_to_wait_for_deployment = call(
            deployment_id=deployment_resource["id"]
        )

        assert model_manager_client.wait_for_deployment.call_args_list == [
            expected_call_to_wait_for_deployment
        ]


class TestLookupDeploymentIdByModelName:
    def test_deployment_does_not_exist(self, model_manager_client: ModelManagerClient):
        with patch.object(
            model_manager_client, "read_deployment_collection"
        ) as mock_read_deployment_collection:
            mock_read_deployment_collection.return_value = {
                "deployments": [
                    make_deployment_resource(random_data=True),
                    make_deployment_resource(random_data=True),
                ]
            }

            return_value = model_manager_client.lookup_deployment_id_by_model_name(
                model_name="unknown-model"
            )

            assert return_value is None

            assert mock_read_deployment_collection.call_count == 1

    def test_deployment_exists(self, model_manager_client: ModelManagerClient):
        with patch.object(
            model_manager_client, "read_deployment_collection"
        ) as mock_read_deployment_collection:
            mock_read_deployment_collection.return_value = {
                "deployments": [
                    make_deployment_resource(),
                    make_deployment_resource(random_data=True),
                    make_deployment_resource(random_data=True),
                ]
            }

            return_value = model_manager_client.lookup_deployment_id_by_model_name(
                model_name="test-model"
            )

            # value taken from make_deployment_resource
            assert return_value == "51125156-c039-460c-9c02-2e3fc0c89da1"

            assert mock_read_deployment_collection.call_count == 1


def object_patch(some_object, attribute_name):
    return patch.object(
        some_object, attribute_name, autospec=getattr(some_object, attribute_name)
    )


class TestCreateDeploymentGracefully:
    """
    Several test cases for ModelManagerClient.ensure_deployment_exists.

    These cases are grouped here to avoid cluttering existing test classes.
    """

    def test_deployment_does_not_yet_exist(
        self, model_manager_client: ModelManagerClient
    ):
        """
        For the case where a deployment does not yet exist, we expect that
        `ensure_deployment_exists` will simply create the deployment.
        """
        model_name = "my_test_model"

        with object_patch(
            model_manager_client, "lookup_deployment_id_by_model_name"
        ) as mock_lookup:
            with object_patch(model_manager_client, "create_deployment") as mock_create:
                # deployment does not exist yet
                mock_lookup.return_value = None

                response = model_manager_client.ensure_deployment_exists(
                    model_name=model_name
                )

                expected_lookup_call = call(model_name)
                assert mock_lookup.call_args_list == [expected_lookup_call]

                expected_deploy_call = call(model_name)
                assert mock_create.call_args_list == [expected_deploy_call]

                # ensure_deployment_exists returns the output of the create_deployment
                # operation
                assert response == mock_create.return_value

    def test_deployment_exists_and_is_healthy(
        self, model_manager_client: ModelManagerClient
    ):
        """
        For the case where a deployment exists and is alive
        (either PENDING or SUCCEEDED), simply return the Deployment resource and do
        nothing else.
        """
        model_name = "my_test_model"
        deployment_id = "4d2eea7a-dcc0-4e0c-81dd-11d35532e595"

        # TODO: check if status flags are OK
        for status in ["PENDING", "SUCCEEDED"]:
            with object_patch(
                model_manager_client, "lookup_deployment_id_by_model_name"
            ) as mock_lookup:
                mock_lookup.return_value = deployment_id

                with object_patch(
                    model_manager_client, "read_deployment_by_id"
                ) as mock_read, object_patch(
                    model_manager_client, "delete_deployment_by_id"
                ) as mock_delete, object_patch(
                    model_manager_client, "create_deployment"
                ) as mock_create:
                    deployment_resource = make_deployment_resource(status)
                    mock_read.return_value = deployment_resource

                    response = model_manager_client.ensure_deployment_exists(model_name)

                    assert mock_lookup.call_args_list == [call(model_name)]

                    assert mock_read.call_args_list == [call(deployment_id)]

                    # No deployment deleted; no new deployment created
                    assert mock_delete.call_count == 0
                    assert mock_create.call_count == 0

                    assert mock_read.return_value == response

    def test_deployment_exists_and_is_unhealthy(
        self, model_manager_client: ModelManagerClient
    ):
        """
        For the case where a deployment exists is and is not healthy (FAILED, STOPPED),
        delete the Deployment and re-create it. The expected return value is the
        return value of the create_deployment call.
        :return:
        """
        model_name = "my_test_model"
        deployment_id = "4d2eea7a-dcc0-4e0c-81dd-11d35532e595"

        for status in ["FAILED", "STOPPED"]:
            with object_patch(
                model_manager_client, "lookup_deployment_id_by_model_name"
            ) as mock_lookup, object_patch(
                model_manager_client, "read_deployment_by_id"
            ) as mock_read, object_patch(
                model_manager_client, "delete_deployment_by_id"
            ) as mock_delete, object_patch(
                model_manager_client, "create_deployment"
            ) as mock_create:
                mock_lookup.return_value = deployment_id
                deployment_resource = make_deployment_resource(status)
                mock_read.return_value = deployment_resource

                response = model_manager_client.ensure_deployment_exists(model_name)

                assert mock_lookup.call_args_list == [call(model_name)]
                assert mock_read.call_args_list == [call(deployment_id)]
                # Deployment deleted and new deployment for model is created
                assert mock_delete.call_args_list == [call(deployment_id)]
                assert mock_create.call_args_list == [call(model_name)]

                assert response == mock_create.return_value


class TestModelManagerClientBusinessBlueprintTemplate:
    def test_read_model_template_collection(self, model_manager_client):
        response = model_manager_client.read_business_blueprint_template_collection()
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/businessBlueprints"
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )

    def test_read_model_template_by_id(self, model_manager_client):
        business_blueprint_id = "4788254b-0bad-4757-a67f-92d5b55f322d"

        response = model_manager_client.read_business_blueprint_template_by_id(
            "4788254b-0bad-4757-a67f-92d5b55f322d"
        )
        assert_get_response_is_json(model_manager_client, response)
        expected_endpoint = "/model-manager/api/v3/businessBlueprints/{}".format(
            business_blueprint_id
        )
        assert_get_from_endpoint_called_with_endpoint(
            model_manager_client, expected_endpoint
        )
