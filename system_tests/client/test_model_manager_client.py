import pytest

from sap.aibus.dar.client.model_manager_client import ModelManagerClient


@pytest.mark.requirements(issues=["42"])
class TestModelManagerClient:
    def test_model_templates(self, model_manager_client: ModelManagerClient):
        expected_model_template_id = "d7810207-ca31-4d4d-9b5a-841a644fd81f"

        templates = model_manager_client.read_model_template_collection()
        assert templates is not None

        assert templates["count"] > 0
        ids = [template["id"] for template in templates["modelTemplates"]]
        assert expected_model_template_id in ids

        a_template = model_manager_client.read_model_template_by_id(
            expected_model_template_id
        )

        assert a_template["id"] == expected_model_template_id

    def test_jobs(self, model_manager_client: ModelManagerClient):
        jobs_collection = model_manager_client.read_job_collection()
        assert "count" in jobs_collection
        assert "jobs" in jobs_collection

        # Other methods are already covered
        # by workflow.test_end_to_end.

    def test_models(self, model_manager_client: ModelManagerClient):
        models_collection = model_manager_client.read_model_collection()
        assert "count" in models_collection
        assert "models" in models_collection

        # read_model_by_name, delete_model_by_name are all already covered
        # by workflow.test_end_to_end.

    def test_deployments(self, model_manager_client: ModelManagerClient):
        deployments_collection = model_manager_client.read_deployment_collection()
        assert "count" in deployments_collection
        assert "deployments" in deployments_collection
