import datetime
import re
from io import BytesIO
from unittest.mock import create_autospec, call, Mock

import pytest

from sap.aibus.dar.client.base_client import BaseClient
from sap.aibus.dar.client.data_manager_client import DataManagerClient
from sap.aibus.dar.client.exceptions import ModelAlreadyExists, DARHTTPException
from sap.aibus.dar.client.util.credentials import (
    StaticCredentialsSource,
    CredentialsSource,
)
from sap.aibus.dar.client.workflow.model import ModelCreator
from sap.aibus.dar.client.model_manager_client import ModelManagerClient
from tests.sap.aibus.dar.client.test_data_manager_client import (
    AbstractDARClientConstruction,
)


@pytest.fixture
def csv_data_stream():
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
    return data_stream


@pytest.fixture()
def create_model():
    create_model = ModelCreator.construct_from_jwt("https://abcd/", token="54321")
    create_model.data_manager_client = create_autospec(DataManagerClient, instance=True)
    create_model.model_manager_client = create_autospec(
        ModelManagerClient, instance=True
    )
    return create_model


@pytest.fixture()
def model_resource():
    return {
        "jobId": "522de4e6-2609-4972-8f75-61e9262b86de",
        "name": "my-model",
        "createdAt": "2018-08-31T11:45:54+00:00",
        "validationResult": {
            "accuracy": 0.9,
            "f1Score": 0.9,
            "precision": 0.9,
            "recall": 0.9,
        },
    }


a_timestamp = datetime.datetime(
    2011, 11, 4, 0, 5, 23, 283000, tzinfo=datetime.timezone.utc
)


class TestModelCreatorClientConstruction(AbstractDARClientConstruction):
    # Tests are in base class
    clazz = ModelCreator

    def test_constructor(self):
        dar_url = "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/"
        source = StaticCredentialsSource("1234")
        client = self.clazz(dar_url, source)
        for embedded_client in [
            client.data_manager_client,
            client.model_manager_client,
        ]:
            assert embedded_client.credentials_source == source

    def test_create_from_jwt(self):
        # Override and change assertions to look into embedded clients.
        jwt = "12345"
        client = self.clazz.construct_from_jwt(self.dar_url, jwt)

        for embedded_client in [
            client.data_manager_client,
            client.model_manager_client,
        ]:
            assert isinstance(
                embedded_client.credentials_source, StaticCredentialsSource
            )
            assert embedded_client.credentials_source.token() == jwt
            assert embedded_client.session.base_url == self.dar_url[:-1]

    def _assert_fields_initialized(self, client):
        assert isinstance(client.data_manager_client, DataManagerClient)
        assert isinstance(client.model_manager_client, ModelManagerClient)
        for embedded_client in [
            client.data_manager_client,
            client.model_manager_client,
        ]:
            assert (
                embedded_client.session.base_url
                == "https://aiservices-dar.cfapps.xxx.hana.ondemand.com"
            )
            assert isinstance(embedded_client.credentials_source, CredentialsSource)


class TestModelCreator:
    def test_is_subclass_of_base_client(self):
        # Should have all the nice construction methods
        assert issubclass(ModelCreator, BaseClient)

    def test_format_dataset_name(self):
        formatted = ModelCreator.format_dataset_name("my-model")
        assert re.match(r"my-model-(\w|-)+", formatted)
        assert len(formatted) <= 255

        # returns a different same for same input on next call
        formatted_2 = ModelCreator.format_dataset_name("my-model")
        assert formatted != formatted_2
        assert len(formatted_2) <= 255

    def test_format_dataset_name_excessive_length_is_truncated(self):
        input_str = "a" * 300
        formatted = ModelCreator.format_dataset_name(input_str)
        assert len(formatted) == 255
        uuid_len = 37
        # First part is still all a's
        assert formatted[:-uuid_len] == input_str[0 : 255 - uuid_len]

    def test_create_model(self, csv_data_stream, create_model, model_resource):
        # inputs
        # model_name: str,

        model_template_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"

        dataset_schema = {
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

        new_dataset_schema_id = "3689fc17-5394-46ba-8757-39a36b570e6e"

        dataset_schema_created = dict(dataset_schema.items())
        dataset_schema_created["id"] = new_dataset_schema_id
        dataset_schema_created["createdAt"] = a_timestamp.isoformat()

        model_name = "my-model"

        dataset_name = model_name + "-123"
        new_dataset_id = "915f16d7-48b0-438b-aca8-048f855ac627"
        dataset_created = {
            "createdAt": a_timestamp.isoformat(),
            "id": new_dataset_id,
            "name": dataset_name,
            "status": "SUCCEEDED",
            "validationMessage": "",
            "datasetSchemaId": new_dataset_schema_id,
        }

        create_model.format_dataset_name = Mock(return_value=dataset_name)

        create_model.data_manager_client.create_dataset_schema.return_value = (
            dataset_schema_created
        )
        create_model.data_manager_client.create_dataset.return_value = dataset_created

        dm = create_model.data_manager_client

        mm = create_model.model_manager_client

        mm.read_model_by_name.side_effect = [
            DARHTTPException(url="https://abcd/", response=Mock(status_code=404)),
            model_resource,
        ]

        # act
        result = create_model.create(
            data_stream=csv_data_stream,
            model_template_id=model_template_id,
            dataset_schema=dataset_schema,
            model_name=model_name,
        )

        assert result == model_resource

        # Expected calls
        expected_create_dataset_schema = call(dataset_schema)
        assert dm.create_dataset_schema.call_args_list == [
            expected_create_dataset_schema
        ]

        expected_dataset_name = dataset_name
        expected_create_dataset = call(
            dataset_name=expected_dataset_name,
            dataset_schema_id=dataset_schema_created["id"],
        )
        assert dm.create_dataset.call_args_list == [expected_create_dataset]

        expected_call_to_upload_and_validate = call(
            dataset_id=dataset_created["id"], data_stream=csv_data_stream
        )
        assert dm.upload_data_and_validate.call_args_list == [
            expected_call_to_upload_and_validate
        ]

        expected_call_to_create_job_and_wait = call(
            model_name=model_name,
            dataset_id=new_dataset_id,
            model_template_id=model_template_id,
        )

        assert mm.create_job_and_wait.call_args_list == [
            expected_call_to_create_job_and_wait
        ]

        expected_call_to_read_model_by_name = call(model_name=model_name)

        assert mm.read_model_by_name.call_args_list == [
            expected_call_to_read_model_by_name,
            expected_call_to_read_model_by_name,
        ]

    def test_create_model_checks_for_existing_model(self, create_model, model_resource):
        """
        If the model already exists, this should be an error.
        """
        model_name = "my-model"

        create_model.model_manager_client.read_model_by_name.return_value = (
            model_resource
        )

        with pytest.raises(ModelAlreadyExists) as context:
            create_model.create(
                data_stream=Mock(),
                model_template_id=Mock(),
                dataset_schema=Mock(),
                model_name=model_name,
            )

        assert "Model 'my-model' already exists" in str(context.value)

        assert create_model.model_manager_client.read_model_by_name.call_args_list == [
            call(model_name=model_name)
        ]

    def test_create_model_forwards_exception(self, create_model, model_resource):
        """
        If ModelManagerClient.read_model_by_name raises a 404 in the initial check,
        this means that the model is not there and execution and proceed. This is
        tested in test_create_model above.

        For all other status code, the exception should be re-raised as is.
        This is tested here.
        """
        model_name = "my-model"

        exc = DARHTTPException(url="https://abcd/", response=Mock(status_code=429))

        create_model.model_manager_client.read_model_by_name.side_effect = exc

        with pytest.raises(DARHTTPException) as context:
            create_model.create(
                data_stream=Mock(),
                model_template_id=Mock(),
                dataset_schema=Mock(),
                model_name=model_name,
            )

        assert context.value == exc

        assert create_model.model_manager_client.read_model_by_name.call_args_list == [
            call(model_name=model_name)
        ]
