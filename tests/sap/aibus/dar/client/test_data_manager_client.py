from io import BytesIO, StringIO
import json
from typing import Any
from unittest.mock import create_autospec, call, Mock, MagicMock

import pytest

from sap.aibus.dar.client.util.credentials import (
    OnlineCredentialsSource,
    StaticCredentialsSource,
)
from sap.aibus.dar.client.dar_session import DARSession
from sap.aibus.dar.client.data_manager_client import DataManagerClient
from sap.aibus.dar.client.exceptions import (
    DatasetInvalidStateException,
    DatasetValidationTimeout,
    DatasetValidationFailed,
    HTTPSRequired,
)
from sap.aibus.dar.client.util.polling import Polling, PollingTimeoutException


class AbstractDARClientConstruction:
    # Must be provided in subclasses!
    clazz = None  # type: Any

    dar_url = "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/"
    clientid = "a-client-id"
    clientsecret = "a-client-secret"
    uaa_url = "https://auth-url"

    def test_constructor(self):
        dar_url = "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/"
        source = StaticCredentialsSource("1234")
        client = self.clazz(dar_url, source)
        assert client.credentials_source == source

    def test_constructor_enforces_https(self):
        dar_url = "http://aiservices-dar.cfapps.xxx.hana.ondemand.com/"
        source = StaticCredentialsSource("1234")
        with pytest.raises(HTTPSRequired):
            self.clazz(dar_url, source)

    def test_constructor_allows_http_localhost(self):
        dar_url = "http://localhost:5001/"
        source = StaticCredentialsSource("1234")
        try:
            self.clazz(dar_url, source)
        except HTTPSRequired:
            assert False, "Plain-text connection to localhost should be allowed."

    def test_create_from_credentials_positional_args(self):
        client = self.clazz.construct_from_credentials(
            self.dar_url, self.clientid, self.clientsecret, self.uaa_url
        )
        self._assert_fields_initialized(client)

    def test_create_from_credentials_keyword_args(self):
        client = self.clazz.construct_from_credentials(
            dar_url=self.dar_url,
            clientid=self.clientid,
            clientsecret=self.clientsecret,
            uaa_url=self.uaa_url,
        )
        self._assert_fields_initialized(client)

    def test_create_from_credentials_enforces_https(self):
        with pytest.raises(HTTPSRequired):
            self.clazz.construct_from_credentials(
                dar_url="http://insecure",
                clientid=self.clientid,
                clientsecret=self.clientsecret,
                uaa_url=self.uaa_url,
            )
        with pytest.raises(HTTPSRequired):
            self.clazz.construct_from_credentials(
                dar_url=self.dar_url,
                clientid=self.clientid,
                clientsecret=self.clientsecret,
                uaa_url="http://insecure-uaa",
            )

    def test_create_from_service_key(self):
        # No kwarg test right now, only for positional API.
        service_key = {
            "uaa": {
                "clientid": self.clientid,
                "clientsecret": self.clientsecret,
                "url": self.uaa_url,
            },
            "url": self.dar_url,
        }
        client = self.clazz.construct_from_service_key(service_key)
        self._assert_fields_initialized(client)

    def test_create_from_service_key_enforces_https(self):
        with pytest.raises(HTTPSRequired):
            # insecure service URL
            service_key = {
                "uaa": {
                    "clientid": self.clientid,
                    "clientsecret": self.clientsecret,
                    "url": self.uaa_url,
                },
                "url": "http://insecure",
            }
            self.clazz.construct_from_service_key(service_key)

        with pytest.raises(HTTPSRequired):
            # insecure UAA url
            service_key = {
                "uaa": {
                    "clientid": self.clientid,
                    "clientsecret": self.clientsecret,
                    "url": "http://insecure",
                },
                "url": self.dar_url,
            }
            self.clazz.construct_from_service_key(service_key)

    def test_create_from_jwt(self):
        jwt = "12345"
        client = self.clazz.construct_from_jwt(self.dar_url, jwt)
        assert isinstance(client.credentials_source, StaticCredentialsSource)
        assert client.credentials_source.token() == jwt
        assert client.session.base_url == self.dar_url[:-1]

    def test_create_from_jwt_enforces_https(self):
        jwt = "12345"
        with pytest.raises(HTTPSRequired):
            # RFC 4266 URLs should also be rejected
            self.clazz.construct_from_jwt("gopher://host:70/1", jwt)

    def test_create_from_cf_env(self, monkeypatch):
        vcap_services = {
            "data-attribute-recommendation-staging": [
                {
                    "binding_guid": "XXXX",
                    "binding_name": None,
                    "credentials": {
                        "swagger": {
                            "dm": self.dar_url + "data-manager/doc/ui",
                            "inference": self.dar_url + "inference/doc/ui",
                            "mm": self.dar_url + "model-manager/doc/ui",
                        },
                        "uaa": {
                            "clientid": self.clientid,
                            "clientsecret": self.clientsecret,
                            "identityzone": "dar-saas-test-app",
                            "identityzoneid": "XXX",
                            "subaccountid": "XXX",
                            "tenantid": "XXX",
                            "tenantmode": "dedicated",
                            "uaadomain": "authentication.sap.hana.ondemand.com",
                            "url": self.uaa_url,
                            "verificationkey": "XXX",
                            "xsappname": "XXX",
                            "zoneid": "XXXX",
                        },
                        "url": self.dar_url,
                    },
                    "instance_guid": "XXX",
                    "instance_name": "dar-instance-3",
                    "label": "data-attribute-recommendation",
                    "name": "dar-instance-3",
                    "plan": "standard",
                    "provider": None,
                    "syslog_drain_url": None,
                    "tags": [],
                    "volume_mounts": [],
                }
            ]
        }

        monkeypatch.setenv("VCAP_SERVICES", json.dumps(vcap_services))
        client = self.clazz.construct_from_cf_env()
        self._assert_fields_initialized(client)

    def _assert_fields_initialized(self, client):
        assert isinstance(client.credentials_source, OnlineCredentialsSource)
        assert client.credentials_source.clientid == self.clientid
        assert client.credentials_source.clientsecret == self.clientsecret
        assert client.credentials_source.url == self.uaa_url
        # Remove trailing slash.
        # TODO: API should just handle combinations of trailing and leading slashes!
        assert client.session.base_url == self.dar_url[:-1]
        assert isinstance(client.session, DARSession)


class TestDataManagerClientConstruction(AbstractDARClientConstruction):
    # Tests are in base class
    clazz = DataManagerClient


class TestDataManagerClientDatasetSchema:
    dar_url = "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/"

    def test_read_dataset_schema_collection(self):
        client = DataManagerClient.construct_from_jwt(self.dar_url, "abcd")

        mock_session = create_autospec(DARSession, instance=True)
        client.session = mock_session

        dataset_schema_example = {
            "createdAt": "2020-02-18T22:18:08.263202+00:00",
            "features": [
                {"label": "manufacturer", "type": "CATEGORY"},
                {"label": "description", "type": "TEXT"},
            ],
            "id": "f6bad1ae-b217-40bb-b7f4-b32a221add9f",
            "labels": [
                {"label": "category", "type": "CATEGORY"},
                {"label": "subcategory", "type": "CATEGORY"},
            ],
            "name": "test",
        }
        dataset_schema_collection = {
            "count": 1,
            "datasetSchemas": [dataset_schema_example],
        }

        expected_api_response = dataset_schema_collection

        mock_response = Mock(spec_set=["json", "status_code"])
        mock_response.json.return_value = dataset_schema_collection
        mock_response.status_code = 200
        mock_session.get_from_endpoint.return_value = mock_response

        observed_result = client.read_dataset_schema_collection()

        expected_url = "/data-manager/api/v3/datasetSchemas"
        expected_get_call = call(expected_url)
        assert mock_session.get_from_endpoint.call_args_list == [expected_get_call]
        assert observed_result == expected_api_response

    def test_read_datasets_collection(self):
        client = self._prepare()

        expected_url = "/data-manager/api/v3/datasets"
        observed_response = client.read_dataset_collection()

        self._assert_get(observed_response, expected_url, client.session)

    def test_read_dataset_schema_by_id(self):
        client = self._prepare()

        identifier = "66e0318b-9637-43ab-84aa-a5eeec87b340"
        expected_url = "/data-manager/api/v3/datasetSchemas/{}".format(identifier)

        observed_response = client.read_dataset_schema_by_id(
            dataset_schema_id=identifier
        )

        self._assert_get(observed_response, expected_url, client.session)

    def test_read_dataset_by_id(self):
        client = self._prepare()

        identifier = "77e0318b-9637-43ab-84aa-a5eeec87b341"
        expected_url = "/data-manager/api/v3/datasets/{}".format(identifier)
        observed_response = client.read_dataset_by_id(dataset_id=identifier)

        self._assert_get(observed_response, expected_url, client.session)

    def test_delete_dataset_by_id(self):
        client = self._prepare()

        identifier = "66e0318b-9637-43ab-84aa-a5eeec87b340"
        expected_url = "/data-manager/api/v3/datasets/{}".format(identifier)

        observed_response = client.delete_dataset_by_id(dataset_id=identifier)

        # So, what do we return when we DELETE? Usually just a 204 or 200 with an
        # empty body?
        assert observed_response is None

        assert client.session.delete_from_endpoint.call_args_list == [
            call(expected_url)
        ]

    def test_delete_dataset_schemas_by_id(self):
        client = self._prepare()

        identifier = "77e0318b-9637-43ab-84aa-a5eeec87b340"
        expected_url = "/data-manager/api/v3/datasetSchemas/{}".format(identifier)

        observed_response = client.delete_dataset_schema_by_id(
            dataset_schema_id=identifier
        )

        # So, what do we return when we DELETE? Usually just a 204 or 200 with an
        # empty body?
        assert observed_response is None

        assert client.session.delete_from_endpoint.call_args_list == [
            call(expected_url)
        ]

    def test_create_dataset_schema(self):
        client = self._prepare()
        expected_url = "/data-manager/api/v3/datasetSchemas"

        observed_response = client.create_dataset_schema(dataset_schema={"a": "b"})

        expected_post_call = call(expected_url, payload={"a": "b"})

        assert client.session.post_to_endpoint.call_args_list == [expected_post_call]
        assert (
            observed_response
            == client.session.post_to_endpoint.return_value.json.return_value
        )

    def test_create_dataset(self):
        client = self._prepare()
        expected_url = "/data-manager/api/v3/datasets"
        dataset_schema_id = "1fd37deb-1add-4cbc-9ec1-cb24d8716472"
        dataset_name = "my dataset"

        observed_response = client.create_dataset(
            dataset_schema_id=dataset_schema_id, dataset_name=dataset_name
        )

        expected_post_call = call(
            expected_url,
            payload={"datasetSchemaId": dataset_schema_id, "name": dataset_name},
        )

        assert client.session.post_to_endpoint.call_args_list == [expected_post_call]
        assert (
            observed_response
            == client.session.post_to_endpoint.return_value.json.return_value
        )

    def test_upload_data_to_dataset(self):
        client = self._prepare()

        expected_url = (
            "/data-manager/api/v3/datasets/a7a1b46a-0295-447e-b6fd-032512b72255/data"
        )

        data_stream = BytesIO(b"CSV;data:")

        observed_response = client.upload_data_to_dataset(
            "a7a1b46a-0295-447e-b6fd-032512b72255", data_stream=data_stream
        )

        expected_put_call = call(expected_url, data_stream=data_stream)

        assert client.session.post_data_to_endpoint.call_args_list == [
            expected_put_call
        ]
        assert (
            observed_response
            == client.session.post_data_to_endpoint.return_value.json.return_value
        )

    def test_upload_data_to_dataset_refuses_strings(self):
        # Method should only accept bytes, but nothing that is decoded - so no str.

        client = self._prepare()

        bad_stream = StringIO("Test! ÄÖÜ!")

        with pytest.raises(ValueError) as exc_info:
            client.upload_data_to_dataset(
                "a7a1b46a-0295-447e-b6fd-032512b72255", data_stream=bad_stream
            )

        exc = exc_info.value
        assert "data_stream argument must use bytes, not str!" in str(exc)

    def _make_dataset_response(self, status):
        return {
            "createdAt": "2020-02-24T08:49:04.351908+00:00",
            "datasetSchemaId": "74a8dc95-974d-43de-99b8-b5ec7a4990b3",
            "id": "f9fc21d9-221c-4626-812c-43a91ade4429",
            "name": "my-dataset",
            "status": status,
            "validationMessage": "",
        }

    def test_wait_for_dataset_validation_uses_polling(self):
        """
        A lower-level test which checks if wait_for_dataset_validation calls
        Polling correctly.

        This test mocks the Polling class entirely.
        """
        client = self._prepare()

        client.read_dataset_by_id = create_autospec(client.read_dataset_by_id)

        polling_class = create_autospec(Polling)
        client.polling_class = lambda: polling_class

        # Act
        dataset_id = "74a8dc95-974d-43de-99b8-b5ec7a4990b3"

        observed_return_value = client.wait_for_dataset_validation(
            dataset_id=dataset_id
        )

        # Assert
        expected_call_to_polling_constructor = call(timeout_seconds=4 * 60 * 60)
        assert polling_class.call_args_list == [expected_call_to_polling_constructor]

        mock_poll_until_success = polling_class.return_value.poll_until_success
        expected_return_value = mock_poll_until_success.return_value
        assert observed_return_value == expected_return_value

        # unpack args to poll_until_success and examine individually
        assert mock_poll_until_success.call_count == 1
        kwargs = mock_poll_until_success.call_args[1]
        # polling_function should be some lambda which internally calls
        # read_dataset_by_id
        polling_function = kwargs["polling_function"]
        # Since we mock Polling, the polling_function and thus read_dataset_by_id is
        # never called
        assert client.read_dataset_by_id.call_count == 0
        # If we invoke the polling_function ourselves, this should call
        # read_dataset_by_id with the dataset_id
        polling_function()
        assert client.read_dataset_by_id.call_count == 1
        success_function = kwargs["success_function"]
        assert success_function == client.is_dataset_validation_finished

        assert client.read_dataset_by_id.call_args == call(dataset_id)

    def test_wait_for_dataset_validation(self):
        """
        Test if method polls until dataset is no longer VALIDATING.

        This uses a real Polling instance, but mocks the Polling.sleep method to
        speed up execution.
        """

        client = self._prepare()

        # This is an alternative Polling constructor
        def polling_constructor(timeout_seconds):
            polling_instance = Polling(timeout_seconds=timeout_seconds)
            polling_instance.sleep = Mock()
            return polling_instance

        client.polling_class = lambda: polling_constructor

        responses = [
            self._make_dataset_response("VALIDATING"),
            self._make_dataset_response("VALIDATING"),
            self._make_dataset_response("SUCCEEDED"),
            # This should never be called
            self._make_dataset_response("BOGUS"),
        ]

        client.session.get_from_endpoint.return_value.json.side_effect = responses

        response = client.wait_for_dataset_validation(
            "11cefce5-097f-4643-acac-b5b28c055915"
        )

        # response should be the last one with SUCCEEDED
        assert response == responses[-2]
        assert client.session.get_from_endpoint.call_count == 3
        expected_get_call = call(
            "/data-manager/api/v3/datasets/11cefce5-097f-4643-acac-b5b28c055915"
        )
        assert client.session.get_from_endpoint.call_args_list == [
            expected_get_call,
            expected_get_call,
            expected_get_call,
        ]

    def test_wait_for_dataset_validation_returns_if_initial_state_is_final(self):
        """
        If the dataset is already in a final state, the method should return
        immediately.
        """
        client = self._prepare()

        client.sleep = Mock()

        responses = [self._make_dataset_response("SUCCEEDED")]

        client.session.get_from_endpoint.return_value.json.side_effect = responses

        response = client.wait_for_dataset_validation(
            "11cefce5-097f-4643-acac-b5b28c055915"
        )

        # response should be the last one with SUCCEEDED
        assert response == responses[0]
        assert client.session.get_from_endpoint.call_count == 1
        expected_get_call = call(
            "/data-manager/api/v3/datasets/11cefce5-097f-4643-acac-b5b28c055915"
        )
        assert client.session.get_from_endpoint.call_args_list == [expected_get_call]

        # Should never be called.
        assert client.sleep.call_count == 0

    def test_wait_for_validation_raises_if_validation_fails(self):
        """
        If the dataset is already in a final state, the method should return
        immediately.
        """
        for bad_dataset_state in ["INVALID_DATA", "VALIDATION_FAILED", "PROGRAM_ERROR"]:
            client = self._prepare()

            client.sleep = Mock()

            dataset_response = self._make_dataset_response(bad_dataset_state)

            if bad_dataset_state == "VALIDATION_FAILED":
                dataset_response["validationMessage"] = "Detailed Description"

            client.session.get_from_endpoint.return_value.json.side_effect = [
                dataset_response
            ]

            with pytest.raises(DatasetValidationFailed) as exc_info:
                client.wait_for_dataset_validation(
                    "11cefce5-097f-4643-acac-b5b28c055915"
                )
            expected_message = (
                "Validation for Dataset "
                "'{}' failed with status '{}' and validation message: '{}'".format(
                    dataset_response["id"],
                    bad_dataset_state,
                    dataset_response["validationMessage"],
                )
            )

            assert str(exc_info.value) == expected_message
            # response should be the last one with SUCCEEDED
            assert client.session.get_from_endpoint.call_count == 1
            expected_get_call = call(
                "/data-manager/api/v3/datasets/11cefce5-097f-4643-acac-b5b28c055915"
            )
            assert client.session.get_from_endpoint.call_args_list == [
                expected_get_call
            ]

            # Should never be called.
            assert client.sleep.call_count == 0

    def test_wait_for_dataset_validation_handles_timeout(self):

        client = self._prepare()

        def mock_polling_class(*args, **kwargs):
            mock_polling = create_autospec(Polling, instance=True)
            mock_polling.poll_until_success.side_effect = PollingTimeoutException
            return mock_polling

        client.polling_class = lambda: mock_polling_class

        with pytest.raises(DatasetValidationTimeout) as exc_info:
            client.wait_for_dataset_validation(
                "11cefce5-097f-4643-acac-b5b28c055915", timeout_seconds=450
            )
        expected_message = (
            "Dataset validation for ID"
            " '11cefce5-097f-4643-acac-b5b28c055915'"
            " did not finish in 450s"
        )
        assert str(exc_info.value) == expected_message

    def test_wait_for_dataset_validation_refuses_invalid_initial_state(self):
        """
        We can only poll a dataset if the dataset is not in state NO_DATA.
        """
        client = self._prepare()

        for bad_status in ["NO_DATA", "UPLOADING"]:
            response = client.session.get_from_endpoint.return_value
            dataset_resource = self._make_dataset_response(bad_status)
            response.json.return_value = dataset_resource

            dataset_id = dataset_resource["id"]
            with pytest.raises(DatasetInvalidStateException) as exc_info:
                client.wait_for_dataset_validation(dataset_id)

            expected = (
                "Cannot wait for Dataset '{}' in status"
                " '{}'! Upload must finish first.".format(dataset_id, bad_status)
            )
            assert expected in str(exc_info.value)

    def test_is_dataset_validation_finished(self):

        # This is an error
        invalid_states = ["NO_DATA", "UPLOADING"]

        unfinished_states = ["VALIDATING"]
        finished_states = [
            "VALIDATION_FAILED",
            "SUCCEEDED",
            "INVALID_DATA",
            "PROGRAM_ERROR",
        ]

        for unfinished_state in unfinished_states:
            data_set = self._make_dataset_response(unfinished_state)
            assert not DataManagerClient.is_dataset_validation_finished(data_set)

        for final_state in finished_states:
            data_set = self._make_dataset_response(final_state)
            assert DataManagerClient.is_dataset_validation_finished(data_set)

        for invalid_state in invalid_states:
            data_set = self._make_dataset_response(invalid_state)

            with pytest.raises(DatasetInvalidStateException) as exc_info:
                DataManagerClient.is_dataset_validation_finished(data_set)

            expected = (
                "Cannot wait for Dataset '{}' in status '{}'!"
                " Upload must finish first."
            ).format(data_set["id"], invalid_state)
            assert expected == str(exc_info.value)

    def test_is_dataset_validation_failed(self):
        non_failed_states = ["SUCCEEDED", "NO_DATA", "UPLOADING", "VALIDATING"]

        failed_states = ["VALIDATION_FAILED", "INVALID_DATA", "PROGRAM_ERROR"]

        for failed_state in failed_states:
            assert DataManagerClient.is_dataset_validation_failed(
                self._make_dataset_response(failed_state)
            )

        for non_failed_state in non_failed_states:
            assert not DataManagerClient.is_dataset_validation_failed(
                self._make_dataset_response(non_failed_state)
            )

    def test_upload_data_to_dataset_and_wait_for_validation(self):
        """
        Tests if upload_data_and_validate calls
        upload_data_to_dataset and wait_for_dataset_validation correctly.
        """
        client = self._prepare()

        client.upload_data_to_dataset = create_autospec(client.upload_data_to_dataset)
        client.wait_for_dataset_validation = create_autospec(
            client.wait_for_dataset_validation
        )

        data_stream = BytesIO(b"abcd")
        dataset_id = "684187a0-a339-4126-9ce1-f161eeed1c02"
        response = client.upload_data_and_validate(
            dataset_id=dataset_id, data_stream=data_stream
        )

        assert response == client.wait_for_dataset_validation.return_value

        expected_upload_call = call(dataset_id, data_stream=data_stream)
        assert client.upload_data_to_dataset.call_args_list == [expected_upload_call]

        expected_wait_call = call(dataset_id)
        assert client.wait_for_dataset_validation.call_args_list == [expected_wait_call]

    def _prepare(self) -> DataManagerClient:
        return prepare_client(self.dar_url, clazz=DataManagerClient)

    def _assert_get(self, api_response, expected_url, mock_session):
        assert mock_session.get_from_endpoint.call_args_list == [call(expected_url)]
        # We expect all methods to return the result of json() on the request Response
        # object.
        assert (
            mock_session.get_from_endpoint.return_value.json.return_value
            == api_response
        )


def prepare_client(dar_url: str, clazz):
    mock_response = MagicMock(spec_set=["json", "status_code"])
    mock_response.status_code = 200
    mock_session = create_autospec(DARSession, instance=True)
    mock_session.get_from_endpoint.return_value = mock_response
    mock_session.post_to_endpoint.return_value = mock_response
    mock_session.post_to_url.return_value = mock_response
    client = clazz.construct_from_jwt(dar_url, "abcd")
    client.session = mock_session
    return client
