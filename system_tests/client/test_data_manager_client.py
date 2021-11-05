from io import BytesIO

import pytest

from sap.aibus.dar.client.data_manager_client import DataManagerClient


@pytest.mark.requirements(issues=["42"])
class TestDataManagerClient:
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

    def test_dataset_schema(self, data_manager_client: DataManagerClient):
        create_response = data_manager_client.create_dataset_schema(
            dataset_schema=self.new_schema
        )
        new_id = create_response["id"]
        read_response = data_manager_client.read_dataset_schema_by_id(new_id)
        assert new_id == read_response["id"]

        all_dataset_schemas = data_manager_client.read_dataset_schema_collection()
        count_before_deletion = all_dataset_schemas["count"]
        assert count_before_deletion > 0

        data_manager_client.delete_dataset_schema_by_id(new_id)
        all_dataset_schemas = data_manager_client.read_dataset_schema_collection()
        count_after_deletion = all_dataset_schemas["count"]
        assert count_before_deletion - count_after_deletion == 1

    def test_dataset(self, data_manager_client: DataManagerClient):
        # Tests dataset functionality without upload
        create_response = data_manager_client.create_dataset_schema(
            dataset_schema=self.new_schema
        )
        new_dataset_schema_id = create_response["id"]

        all_datasets = data_manager_client.read_dataset_collection()
        prev_count = all_datasets["count"]

        new_dataset_response = data_manager_client.create_dataset(
            dataset_schema_id=new_dataset_schema_id, dataset_name="my-dataset"
        )

        assert new_dataset_response["name"] == "my-dataset"
        assert new_dataset_response["datasetSchemaId"] == new_dataset_schema_id
        assert new_dataset_response["status"] == "NO_DATA"

        new_dataset_id = new_dataset_response["id"]

        all_datasets = data_manager_client.read_dataset_collection()
        new_count = all_datasets["count"]

        assert new_count == prev_count + 1

        data_manager_client.delete_dataset_by_id(new_dataset_id)
        data_manager_client.delete_dataset_schema_by_id(new_dataset_schema_id)

        all_datasets = data_manager_client.read_dataset_collection()
        after_deletion_count = all_datasets["count"]

        assert after_deletion_count == new_count - 1

    @pytest.mark.requirements(issues=["42"])
    def test_dataset_upload(self, data_manager_client: DataManagerClient):
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

        create_response = data_manager_client.create_dataset_schema(
            dataset_schema=self.new_schema
        )
        new_dataset_schema_id = create_response["id"]

        new_dataset_response = data_manager_client.create_dataset(
            dataset_schema_id=new_dataset_schema_id, dataset_name="my-dataset"
        )

        new_dataset_id = new_dataset_response["id"]

        response = data_manager_client.upload_data_and_validate(
            new_dataset_id, data_stream
        )
        assert response["status"] == "SUCCEEDED"

        data_manager_client.delete_dataset_by_id(new_dataset_id)
        data_manager_client.delete_dataset_schema_by_id(new_dataset_schema_id)
