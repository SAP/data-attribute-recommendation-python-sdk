"""
Train a model from a CSV file.
"""
import typing
import uuid

from sap.aibus.dar.client.base_client import BaseClient
from sap.aibus.dar.client.data_manager_client import DataManagerClient
from sap.aibus.dar.client.exceptions import ModelAlreadyExists, DARHTTPException
from sap.aibus.dar.client.model_manager_client import ModelManagerClient
from sap.aibus.dar.client.util.credentials import CredentialsSource


class ModelCreator(BaseClient):
    """
    This class provides a high-level means of training a model from a CSV file.

    To construct an instance of this class, see the various *construct_* methods
    such as
    :meth:`~sap.aibus.dar.client.base_client.BaseClient.construct_from_credentials`
    in :class:`~sap.aibus.dar.client.base_client.BaseClient`.

    Internally, the class wraps and orchestrates :class:`DataManagerClient` and
    :class:`ModelManagerClient`.
    """

    def __init__(self, url: str, source: CredentialsSource):
        self.data_manager_client = DataManagerClient(url=url, credentials_source=source)
        self.model_manager_client = ModelManagerClient(
            url=url, credentials_source=source
        )

    def create(
        self,
        data_stream: typing.BinaryIO,
        model_template_id: str,
        dataset_schema: dict,
        model_name: str,
    ) -> dict:
        """
        Trains a model from a CSV file.

        Internally, this method creates the required DatasetSchema and Dataset entities,
        uploads the data and starts the training job. The method will block until
        the training job finishes.

        Once this method returns, the model `model_name` can be deployed and used
        for inference.

        This method will raise an Exception if an error occurs.

        **No** clean up is performed: if for example a *TrainingJobFailed* or
        *TrainingJobTimeOut* exception occurs, the previously created Dataset
        and DatasetSchema will remain within the service and must be cleaned up
        manually.

        :param data_stream: binary stream containing a CSV file in UTF-8 encoding
        :param model_template_id: the model template ID
        :param dataset_schema: dataset schema as dict
        :param model_name: name of the model to be trained
        :raises TrainingJobFailed: When training job has status FAILED
        :raises TrainingJobTimeOut: When training job takes too long
        :raises: DatasetValidationTimeout: if validation takes too long
        :raises: DatasetValidationFailed: if validation does not finish in state
                *SUCCEEDED*
        :raises: ModelAlreadyExists: if model already exists at start of process
        :return:
        """

        self.log.info("Checking if model exists")
        try:
            self.model_manager_client.read_model_by_name(model_name=model_name)
        except DARHTTPException as exception:
            if exception.status_code == 404:
                pass
            else:
                raise
        else:
            raise ModelAlreadyExists(model_name)

        self.log.info("Creating DatasetSchema.")
        response_dataset_schema = self.data_manager_client.create_dataset_schema(
            dataset_schema
        )
        dataset_schema_id = response_dataset_schema["id"]
        self.log.info("Created dataset schema with id '%s'", dataset_schema_id)

        dataset_name = self.format_dataset_name(model_name)
        self.log.info("Creating Dataset with name '%s'", dataset_name)

        response_dataset = self.data_manager_client.create_dataset(
            dataset_name=dataset_name, dataset_schema_id=dataset_schema_id
        )

        dataset_id = response_dataset["id"]
        self.log.info("Created Dataset with id '%s'", dataset_id)

        self.log.info("Uploading data to Dataset '%s'", dataset_id)

        self.data_manager_client.upload_data_and_validate(
            dataset_id=dataset_id, data_stream=data_stream
        )
        self.log.info(
            "Data uploaded and validated successfully for dataset '%s'", dataset_id
        )

        self.log.info("Starting training job.")
        response_job_creation = self.model_manager_client.create_job_and_wait(
            model_name=model_name,
            dataset_id=dataset_id,
            model_template_id=model_template_id,
        )
        self.log.info(
            "Training finished successfully. Job ID: '%s'", response_job_creation["id"]
        )

        model = self.model_manager_client.read_model_by_name(model_name=model_name)
        self.log.debug("Final model resource: '%s'", model)
        return model

    @staticmethod
    def format_dataset_name(model_name: str) -> str:
        """
        Derives a Dataset name from a Model name.

        For the purpose of automation, we automatically create a Dataset name from
        a Model name.

        Return value has no more than 255 characters.

        :param model_name: Model name
        :return: suitable Dataset name
        """
        random_string = "-" + str(uuid.uuid4())
        return (
            model_name[0 : 255 - len(model_name) - len(random_string)] + random_string
        )
