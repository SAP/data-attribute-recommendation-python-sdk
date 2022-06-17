"""
Client API for the Model Manager microservice.
"""

# pylint: disable=fixme


import typing

from sap.aibus.dar.client.base_client import BaseClientWithSession
from sap.aibus.dar.client.exceptions import (
    TrainingJobFailed,
    TrainingJobTimeOut,
    DeploymentTimeOut,
    DeploymentFailed,
    CreateTrainingJobFailed,
    JobNotFound,
)
from sap.aibus.dar.client.model_manager_constants import (
    JobStatus,
    DeploymentStatus,
    ModelManagerPaths,
)
from sap.aibus.dar.client.util.polling import Polling, PollingTimeoutException

#: How long to wait for a deployment to succeed.
TIMEOUT_DEPLOYMENT_SECONDS = 30 * 60

#: How frequently to poll a deployment for its status
INTERVALL_DEPLOYMENT_SECONDS = 45

#: How long to wait for a training job to succeed.
TIMEOUT_TRAINING_JOB_SECONDS = 24 * 60 * 60

#: How frequently to poll a training job for its status
INTERVALL_TRAINING_JOB_SECONDS = 60


class ModelManagerClient(BaseClientWithSession):
    """
    The client class for the DAR ModelManager microservice.

    This class implements all basic API calls as well as some convenience methods
    which wrap individual API calls.

    All methods return the JSON response returned by the server as dict, unless
    indicated otherwise.

    If a HTTP API call fails, all methods will raise an :exc:`DARHTTPException`.
    """

    # pylint:disable=too-many-public-methods

    @staticmethod
    def polling_class() -> typing.Type[Polling]:
        """
        Returns the Polling implementation used to
        wait on asynchronous processes.

        This is rarely of interest to the end-user.

        :return: Polling implementation
        """
        return Polling

    def read_model_template_collection(self) -> dict:
        """
        Reads the collection of ModelTemplates.

        For details, see the section on `Model Templates`_ in the
        official DAR documentation.

        .. _Model Templates:
            https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/1e76e8c636974a06967552c05d40e066.html

        :return: ModelTemplate collection as dict
        """
        response = self.session.get_from_endpoint(
            ModelManagerPaths.ENDPOINT_MODEL_TEMPLATE_COLLECTION
        )
        return response.json()

    def read_model_template_by_id(self, model_template_id: str) -> dict:
        """
        Reads the ModelTemplate with the given *model_template_id*.

        For details, see the section on `Model Templates`_ in the
        official DAR documentation.

        :param model_template_id: ID of the ModelTemplate to be retrieved
        :return: a single ModelTemplate as dict
        """
        endpoint = ModelManagerPaths.format_model_templates_endpoint_by_id(
            model_template_id
        )
        response = self.session.get_from_endpoint(endpoint)
        return response.json()

    def read_job_collection(self) -> dict:
        """
        Reads the collection of all Jobs.

        :return: Job collection as dict
        """
        response = self.session.get_from_endpoint(
            ModelManagerPaths.ENDPOINT_JOB_COLLECTION
        )
        return response.json()

    def read_job_by_id(self, job_id: str) -> dict:
        """
        Reads the Job with the given *job_id*.

        :param job_id: ID of the Job to be retrieved.
        :return: a single Job as dict
        :raises JobNotFound: when no Job with given model name is found
        """
        endpoint = ModelManagerPaths.format_job_endpoint_by_id(job_id)
        response = self.session.get_from_endpoint(endpoint)
        return response.json()

    def read_job_by_model_name(self, model_name: str) -> dict:
        """
        Reads Job with the given *model_name*
        :param model_name: name of model
        :return: a single Job as dict
        :raises
        """
        jobs_response = self.read_job_collection()
        jobs = jobs_response["jobs"]
        for job in jobs:
            if job["modelName"] == model_name:
                return job
        raise JobNotFound(
            "Job with model name '{}' could not be found".format(model_name)
        )

    def delete_job_by_id(self, job_id: str) -> None:
        """
        Deletes the Job with the given *job_id*.

        Will raise a :exc:`DARHTTPException` if operation fails.

        :param job_id: ID of the Job to be deleted
        :return: None
        :raise `DARHTTPException`: if server returned an error
        """
        self.log.info("Deleting Job with ID '%s'", job_id)
        endpoint = ModelManagerPaths.format_job_endpoint_by_id(job_id)
        self.session.delete_from_endpoint(endpoint)

    def create_job(
        self,
        model_name: str,
        dataset_id: str,
        model_template_id: str = None,
        business_blueprint_id: str = None,
    ) -> dict:
        """
        Creates a training Job.

        A training Job is an asynchronous process and can take a few minutes or even
        several hours, depending on the data set and the system load.

        Initially, the training job will be in status *RUNNING* or *PENDING*. Use
        :meth:`read_job_by_id` to poll for status changes. Alternatively, use
        :meth:`wait_for_job` to wait for the job to succeed.

        A convenience method is available at :meth:`create_job_and_wait` which will
        submit a job and wait for its completion.

        :param model_name: Name of the model to train
        :param dataset_id: Id of previously uploaded, valid dataset
        :param model_template_id: Model template ID for training
        :param business_blueprint_id: Business Blueprint template ID for training
        :raises CreateTrainingJobFailed: When business_blueprint_id
            and model_template_id are provided or when both are not provided
        :return: newly created Job as dict
        """
        self.log.info(
            "Creating job with model_name: %s, dataset_id: %s, model_template_id: %s",
            model_name,
            dataset_id,
            model_template_id,
        )
        if business_blueprint_id and model_template_id:
            raise CreateTrainingJobFailed(
                "Either model_template_id or business_blueprint_id"
                " have to be specified, not both."
            )
        if not business_blueprint_id and not model_template_id:
            raise CreateTrainingJobFailed(
                "Either model_template_id or business_blueprint_id"
                " have to be specified."
            )
        if business_blueprint_id:
            payload = {
                "modelName": model_name,
                "datasetId": dataset_id,
                "businessBlueprintId": business_blueprint_id,
            }
        elif model_template_id:
            payload = {
                "modelName": model_name,
                "datasetId": dataset_id,
                "modelTemplateId": model_template_id,
            }
        response = self.session.post_to_endpoint(
            ModelManagerPaths.ENDPOINT_JOB_COLLECTION, payload=payload
        )
        response_as_json = response.json()

        self.log.info("Created job with id %s", response_as_json["id"])
        return response_as_json

    def create_job_and_wait(
        self,
        model_name: str,
        dataset_id: str,
        model_template_id: str = None,
        business_blueprint_id: str = None,
    ):
        """
        Starts a job and waits for the job to finish.

        This method is a thin wrapper around :meth:`create_job` and
        :meth:`wait_for_job`.

        :param model_name: Name of the model to train
        :param dataset_id: Id of previously uploaded, valid dataset
        :param model_template_id: Model template ID for training
        :param business_blueprint_id: Business Blueprint ID for training
        :raises TrainingJobFailed: When training job has status FAILED
        :raises TrainingJobTimeOut: When training job takes too long
        :return: API response as dict
        """
        job_resource = self.create_job(
            model_name=model_name,
            dataset_id=dataset_id,
            model_template_id=model_template_id,
            business_blueprint_id=business_blueprint_id,
        )
        return self.wait_for_job(job_resource["id"])

    def wait_for_job(self, job_id: str) -> dict:
        """
        Waits for a job to finish.

        :param job_id: ID of job
        :raises TrainingJobFailed: When training job has status FAILED
        :raises TrainingJobTimeOut: When training job takes too long
        :returns: Job resource from last API call
        """
        clazz = self.polling_class()
        timeout_seconds = TIMEOUT_TRAINING_JOB_SECONDS
        polling = clazz(
            timeout_seconds=timeout_seconds,
            intervall_seconds=INTERVALL_TRAINING_JOB_SECONDS,
        )

        def polling_function():
            self.log.info("Polling for status of job '%s'", job_id)
            job_resource = self.read_job_by_id(job_id)
            self.log.info(
                "Job '%s': status '%s', progress: '%s'",
                job_id,
                job_resource["status"],
                job_resource["progress"],
            )
            return job_resource

        self.log.info("Waiting for job '%s' to finish.", job_id)

        try:
            result = polling.poll_until_success(
                polling_function=polling_function, success_function=self.is_job_finished
            )
        except PollingTimeoutException as timeout_exception:
            timeout_msg = "Training job '{}' did not finish within {}s".format(
                job_id, timeout_seconds
            )
            self.log.exception(timeout_msg)
            raise TrainingJobTimeOut(timeout_msg) from timeout_exception

        msg = "Job '{}' has status: '{}'".format(job_id, result["status"])
        if self.is_job_failed(result):
            self.log.error(msg)
            raise TrainingJobFailed(msg)

        self.log.info(msg)

        return result

    @staticmethod
    def is_job_finished(job_resource: dict) -> bool:
        """
        Returns True if a Job has a final state.

        This does not imply that the Job was successful; it merely
        checks if the process has finished.

        Also see :meth:`is_job_failed`.

        :param job_resource: Job resource as returned by API
        :return: True if Job is in final state
        """
        if job_resource["status"] in [
            JobStatus.SUCCEEDED.value,
            JobStatus.FAILED.value,
        ]:
            return True
        return False

    @staticmethod
    def is_job_failed(job_resource: dict) -> bool:
        """
        Returns True if a Job has failed.

        A return value of False does not imply that the Job has finished
        successfully. The Job is simply in a non-failed state, e.g. in
        *RUNNING*.

        Also see :meth:`is_job_finished`.

        :param job_resource: Job resource as returned by API
        :return: True if Job has failed
        """
        return job_resource["status"] == JobStatus.FAILED.value

    def read_model_collection(self) -> dict:
        """
        Reads the collection of trained Models.

        :return: Model collection as dict
        """
        response = self.session.get_from_endpoint(
            ModelManagerPaths.ENDPOINT_MODEL_COLLECTION
        )
        return response.json()

    def read_model_by_name(self, model_name: str) -> dict:
        """
        Reads a Model by name.

        :param model_name: name of Model
        :return: a single Model as dict
        """
        response = self.session.get_from_endpoint(
            ModelManagerPaths.format_model_endpoint_by_name(model_name)
        )
        return response.json()

    def delete_model_by_name(self, model_name: str) -> None:
        """
        Deletes a Model by name.

        :param model_name: name of Model to be deleted
        :return: None
        """
        self.log.info("Deleting Model with name '%s'", model_name)

        endpoint = ModelManagerPaths.format_model_endpoint_by_name(model_name)
        self.session.delete_from_endpoint(endpoint)

    def read_deployment_collection(self) -> dict:
        """
        Reads the collection of Deployments.

        A deployment is a deployed Model and can be used for Inference.

        :return: Deployment collection as dict
        """
        response = self.session.get_from_endpoint(
            ModelManagerPaths.ENDPOINT_DEPLOYMENT_COLLECTION
        )
        return response.json()

    def read_deployment_by_id(self, deployment_id: str) -> dict:
        """
        Reads a Deployment by ID.

        :param deployment_id: ID of the Deployment
        :return: a single Deployment as dict
        """
        response = self.session.get_from_endpoint(
            ModelManagerPaths.format_deployment_endpoint_by_id(deployment_id)
        )
        return response.json()

    def create_deployment(self, model_name: str) -> dict:
        """
        Creates a Deployment for the given model_name.

        The creation of a Deployment is an asynchronous process and can take
        several minutes.

        Initially, the Deployment will be in status *PENDING*. Use
        :meth:`read_deployment_by_id` or the higher-level :meth:`wait_for_deployment`
        to poll for status changes.

        :param model_name: name of the Model to deploy
        :return: a single Deployment as dict
        """
        self.log.info("Creating Deployment for model_name '%s'", model_name)
        payload = {"modelName": model_name}
        response = self.session.post_to_endpoint(
            ModelManagerPaths.ENDPOINT_DEPLOYMENT_COLLECTION, payload=payload
        )
        response_as_json = response.json()
        self.log.info(
            "Created Deployment for model_name '%s' with ID '%s'",
            model_name,
            response_as_json["id"],
        )
        return response.json()

    def delete_deployment_by_id(self, deployment_id: str) -> None:
        """
        Deletes a Deployment by ID.

        To delete a Deployment by Model name, see :meth:`ensure_model_is_undeployed`.

        :param deployment_id: ID of the Deployment to be deleted
        :return: None
        """
        self.log.info("Deleting Deployment with ID '%s'", deployment_id)
        endpoint = ModelManagerPaths.format_deployment_endpoint_by_id(deployment_id)
        self.session.delete_from_endpoint(endpoint)

    def ensure_model_is_undeployed(self, model_name: str) -> typing.Optional[str]:
        """
        Ensures that a Model is not deployed.

        If the given Model is deployed, the Deployment is deleted. The status
        of the Deployment is not considered here. Returns the Deployment ID
        in this case.

        If the Model is not deployed, the method does nothing. It is not an error
        if the Model is not deployed. Returns *None* if the Model is not
        deployed.

        This method is a thin wrapper around :meth:`lookup_deployment_id_by_model_name`
        and :meth:`delete_deployment_by_id`.

        :param model_name: name of the model to undeploy
        :return: ID of the deleted Deployment or None
        """
        deployment_id = self.lookup_deployment_id_by_model_name(model_name)
        if deployment_id is not None:
            self.log.info(
                "Deployment '%s' found for model_name '%s'. Undeploying!",
                deployment_id,
                model_name,
            )
            self.delete_deployment_by_id(deployment_id)
            return deployment_id

        self.log.info(
            "No deployment found for model_name '%s'. Not undeploying.", deployment_id
        )
        return None

    def wait_for_deployment(self, deployment_id: str) -> dict:
        """
        Waits for a deployment to succeed.

        Raises a :exc:`DeploymentTimeOut` if the Deployment process does not
        finish within a given timeout (:const:`TIMEOUT_DEPLOYMENT_SECONDS`).
        Even after the exception has been raised, the Deployment can still succeed
        in the background even.

        .. note ::

            A Deployment in status *SUCCEEDED* can incur costs.

        :param deployment_id: ID of the Deployment
        :raises DeploymentTimeOut: If Deployment does not finish within timeout
        :raises DeploymentFailed: If Deployment fails
        :return: Deployment resource as returned by final API call
        """
        polling_clazz = self.polling_class()
        polling = polling_clazz(
            intervall_seconds=INTERVALL_DEPLOYMENT_SECONDS,
            timeout_seconds=TIMEOUT_DEPLOYMENT_SECONDS,
        )

        def polling_function():
            self.log.debug("Polling status for deployment '%s'", deployment_id)
            return self.read_deployment_by_id(deployment_id)

        self.log.info("Waiting for Deployment ID '%s' to succeed!", deployment_id)

        try:
            response = polling.poll_until_success(
                polling_function=polling_function,
                success_function=self.is_deployment_finished,
            )
        except PollingTimeoutException as exc:
            msg = "Deployment '{}' did not succeed within {}s".format(
                deployment_id, TIMEOUT_DEPLOYMENT_SECONDS
            )
            self.log.exception(msg)
            raise DeploymentTimeOut(msg) from exc

        msg = "Deployment '{}' has status: {}".format(deployment_id, response["status"])
        if self.is_deployment_failed(response):
            self.log.error(msg)
            raise DeploymentFailed(msg)

        self.log.info(msg)

        return response

    def deploy_and_wait(self, model_name: str) -> dict:
        """
        Deploys a Model and waits for Deployment to succeed.

        This method is a thin wrapper around :meth:`create_deployment`
        and :meth:`wait_for_deployment`.

        :param model_name: Name of the Model to deploy
        :raises DeploymentTimeOut: If Deployment does not finish within timeout
        :raises DeploymentFailed: If Deployment fails
        :return: Model resource from final API call
        """
        deployment = self.create_deployment(
            model_name=model_name,
        )
        deployment_id = deployment["id"]
        assert deployment_id is not None  # for mypy
        self.log.debug(
            "Created deployment '%s' for model '%s'", deployment_id, model_name
        )
        return self.wait_for_deployment(deployment_id=deployment_id)

    def ensure_deployment_exists(self, model_name: str) -> dict:
        """
        Ensures a Deployment exists and is not failed.

        Deploys the given *model_name* if not Deployment exists yet.
        If the Deployment is in a failed state, the existing Deployment is deleted and
        a new Deployment is created.

        Note that the newly created Deployment will be in state *PENDING*.
        See the remarks on :meth:`create_deployment` and :meth:`wait_for_deployment`.

        :param model_name: Name of the Model to deploy
        :return: Deployment resource
        """

        existing_deployment_id = self.lookup_deployment_id_by_model_name(model_name)
        if not existing_deployment_id:
            self.log.info(
                "No Deployment found for model_name '%s'."
                " Created new Deployment '%s'",
                model_name,
                existing_deployment_id,
            )
            return self.create_deployment(model_name)

        existing_deployment = self.read_deployment_by_id(existing_deployment_id)
        if self.is_deployment_failed(existing_deployment):
            self.log.info(
                "Deployment '%s' for Model '%s' is failed."
                " Re-creating the Deployment",
                existing_deployment_id,
                model_name,
            )
            self.delete_deployment_by_id(existing_deployment_id)

            new_deployment = self.create_deployment(model_name)
            new_deployment_id = new_deployment["id"]
            self.log.info(
                "Created new Deployment '%s' for Model '%s'",
                new_deployment_id,
                model_name,
            )
            return new_deployment

        return existing_deployment

    def lookup_deployment_id_by_model_name(
        self, model_name: str
    ) -> typing.Optional[str]:
        """
        Returns the Deployment ID for a given Model name.

        If the Model is not deployed, this will return None.

        :param model_name: name of the Model to check
        :return: Deployment ID or None
        """
        all_deployments = self.read_deployment_collection()
        for deployment in all_deployments["deployments"]:
            if deployment["modelName"] == model_name:
                self.log.info(
                    "Found Deployment ID '%s' for Model named '%s'",
                    deployment["id"],
                    model_name,
                )
                return deployment["id"]
        return None

    @staticmethod
    def is_deployment_finished(deployment_resource: dict):
        """
        Returns True if a Deployment has a final state.

        This does not imply that the Deployment is operational; it merely
        checks if the creation of the Deployment failed or succeeded.

        Also see :meth:`is_deployment_failed`.

        :param deployment_resource: Deployment resource as returned by API
        :return: True if Deployment has final state
        """
        # TODO: raise error on missing "status" saying that this must come from
        # "read_by_id", not "read_collection"
        return deployment_resource["status"] != DeploymentStatus.PENDING.value

    @staticmethod
    def is_deployment_failed(deployment_resource: dict):
        """
        Returns True if a Deployment has failed.

        A return value of False does not imply that the Deployment is operational.
        The Deployment can also be in state *PENDING*.

        Also see :meth:`is_deployment_finished`.

        :param deployment_resource: Deployment resource as returned by API
        :return: True if Deployment is failed
        """
        return deployment_resource["status"] in [
            DeploymentStatus.STOPPED.value,
            DeploymentStatus.FAILED.value,
        ]

    def read_business_blueprint_template_collection(self) -> dict:
        """
        Reads the collection of BusinessBlueprint Template.
        :return: BusinessBlueprint collection as dict
        """
        response = self.session.get_from_endpoint(
            ModelManagerPaths.ENDPOINT_BUSINESS_BLUEPRINT_TEMPLATE_COLLECTION
        )
        return response.json()

    def read_business_blueprint_template_by_id(
        self, business_blueprint_id: str
    ) -> dict:
        """
        Reads the BusinessBlueprintTemplate with the given *business_blueprint_id*.
        :param business_blueprint_id: ID of the BusinessBlueprint to be retrieved
        :return: a single BusinessBlueprintTemplate as dict
        """
        endpoint = ModelManagerPaths.format_business_blueprint_endpoint_by_id(
            business_blueprint_id
        )
        response = self.session.get_from_endpoint(endpoint)
        return response.json()
