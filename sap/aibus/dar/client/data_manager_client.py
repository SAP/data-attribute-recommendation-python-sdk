"""
Client API for the Data Manager microservice.
"""

# pylint: disable=fixme
# TODO: Remove these
import typing

from sap.aibus.dar.client.base_client import BaseClientWithSession
from sap.aibus.dar.client.data_manager_constants import DatasetStatus, DataManagerPaths
from sap.aibus.dar.client.exceptions import (
    DatasetInvalidStateException,
    DatasetValidationTimeout,
    DatasetValidationFailed,
)
from sap.aibus.dar.client.util.polling import Polling, PollingTimeoutException

#: How long to wait for a dataset validation job to succeed.
TIMEOUT_DATASET_VALIDATION = 3600 * 4


class DataManagerClient(BaseClientWithSession):
    """
    The client class for the DAR DataManager microservice.

    This class implements all basic API calls as well as some convenience methods
    which wrap individual API calls.

    All methods return the JSON response returned by the server as dict, unless
    indicated otherwise.

    If a HTTP API call fails, all methods will raise an :exc:`DARHTTPException`.
    """

    @staticmethod
    def polling_class() -> typing.Type[Polling]:
        """
        Returns the Polling implementation used to
        wait on asynchronous processes.

        This is rarely of interest to the end-user.

        :return: Polling implementation
        """
        return Polling

    def create_dataset_schema(self, dataset_schema: dict) -> dict:
        """
        Creates a DatasetSchema.

        :param dataset_schema: a DatasetSchema as python dict
        :return: the newly created DatasetSchema as dict
        """
        self.log.info("Creating DatasetSchema.")
        endpoint = DataManagerPaths.ENDPOINT_DATASET_SCHEMA_COLLECTION
        response = self.session.post_to_endpoint(endpoint, payload=dataset_schema)
        response_as_json = response.json()
        self.log.info("Created DatasetSchema with ID '%s'", response_as_json["id"])
        return response_as_json

    def read_dataset_schema_collection(self) -> dict:
        """
        Reads the collection of DatasetSchemas.

        :return: Dataset collection as dict
        """
        endpoint = DataManagerPaths.ENDPOINT_DATASET_SCHEMA_COLLECTION
        response = self.session.get_from_endpoint(endpoint)
        return response.json()

    def read_dataset_schema_by_id(self, dataset_schema_id: str) -> dict:
        """
        Reads the DatasetSchema with the given *dataset_schema_id*.

        :param dataset_schema_id: ID of the DatasetSchema to be retrieved
        :return: a single DatasetSchema as dict
        """
        endpoint = DataManagerPaths.format_dataset_schemas_endpoint_by_id(
            dataset_schema_id
        )
        response = self.session.get_from_endpoint(endpoint)
        return response.json()

    def delete_dataset_schema_by_id(self, dataset_schema_id: str) -> None:
        """
        Deletes the DatasetSchema with the given *dataset_schema_id*.

        :param dataset_schema_id: ID of the DatasetSchema to be deleted
        :return: None
        """
        self.log.info("Deleting DatasetSchema with ID '%s'", dataset_schema_id)
        endpoint = DataManagerPaths.format_dataset_schemas_endpoint_by_id(
            dataset_schema_id
        )
        self.session.delete_from_endpoint(endpoint)

    def create_dataset(self, dataset_name: str, dataset_schema_id: str) -> dict:
        """
        Creates a Dataset with the given **dataset_name** and **dataset_schema_id**.

        The **dataset_schema_id** must reference a previously created DatasetSchema
        (see :meth:`create_dataset_schema`).

        :param dataset_name: Name of the Dataset to be created
        :param dataset_schema_id: ID of DatasetSchema used for the Dataset
        :return: the newly created DatasetSchema as dict
        """
        self.log.info(
            "Creating Dataset with dataset_name '%s' and dataset_schema_id '%s'",
            dataset_name,
            dataset_schema_id,
        )
        endpoint = DataManagerPaths.ENDPOINT_DATASET_COLLECTION
        payload = {"datasetSchemaId": dataset_schema_id, "name": dataset_name}
        response = self.session.post_to_endpoint(endpoint, payload=payload)
        response_as_json = response.json()
        self.log.info("Created Dataset with ID '%s'", response_as_json["id"])
        return response_as_json

    def read_dataset_collection(self) -> dict:
        """
        Reads the collection of Datasets.

        :return: Dataset collection as dict
        """
        endpoint = DataManagerPaths.ENDPOINT_DATASET_COLLECTION
        response = self.session.get_from_endpoint(endpoint)
        return response.json()

    def read_dataset_by_id(self, dataset_id: str) -> dict:
        """
        Reads the Dataset identified by the given *dataset_id*.

        :param dataset_id: ID of the Dataset to be retrieved
        :return: Dataset as dict
        """
        endpoint = DataManagerPaths.format_dataset_endpoint_by_id(dataset_id)
        response = self.session.get_from_endpoint(endpoint)
        return response.json()

    def delete_dataset_by_id(self, dataset_id: str) -> None:
        """
        Deletes the Dataset identified by *dataset_id*.


        :param dataset_id: ID of the Dataset to be deleted
        :return: None
        """
        self.log.info("Deleting Dataset with ID '%s'", dataset_id)
        endpoint = DataManagerPaths.format_dataset_endpoint_by_id(dataset_id)
        self.session.delete_from_endpoint(endpoint)

    def upload_data_to_dataset(
        self, dataset_id: str, data_stream: typing.BinaryIO
    ) -> dict:
        """
        Uploads data to a Dataset.

        Data can only be uploaded once per Dataset. If the Dataset status is
        not **NO_DATA**, the server will return a corresponding error message.

        During the upload process, the Dataset will have status **UPLOADING**.
        In this state, it is not possible to delete the Dataset. If the upload is
        interrupted (i.e. due to network problems), please wait for fifteen minutes
        before deleting the dataset. After fifteen minutes, it is possible to delete
        the Dataset even if it is in status **UPLOADING**.

        After the upload, the status of the dataset will be **VALIDATING**.

        Data upload is an asynchronous process. After data upload, the dataset
        will be validated in a background process.

        Use :meth:`read_dataset_by_id` to poll the dataset until
        :meth:`is_dataset_validation_finished` returns *True*.
        An implementation of this algorithm is available in
        :meth:`wait_for_dataset_validation`.

        A blocking version of entire process including upload and validation
        is available in :meth:`upload_data_and_validate`.

        The *data_stream* parameter must be a stream which returns bytes. When reading
        from a file, simply open the file in **binary** mode::

            file_handle = open("my_file.csv", mode='rb')
            client.upload_data_to_dataset(
                'your-dataset-identifier',
                file_handle
            )

        .. note::

            The file must already be encoded in UTF-8 format. The DAR service only
            supports UTF-8. If you are using a GZIP file, ensure the content of the file
            prior to compression is encoded as UTF-8. If the file is not encoded as
            UTF-8, the service will reject the file during validation.

        :param dataset_id: identifier of the dataset
        :param data_stream: a data stream returning bytes
        :return: API response as dict
        """
        if hasattr(data_stream, "encoding"):
            raise ValueError(
                "data_stream argument must use bytes, not str! Received: '%s'"
                % data_stream
            )
        self.log.info("Uploading data for dataset_id '%s'", dataset_id)
        endpoint = DataManagerPaths.format_data_endpoint_by_id(dataset_id)
        response = self.session.post_data_to_endpoint(endpoint, data_stream=data_stream)
        return response.json()

    def wait_for_dataset_validation(
        self, dataset_id: str, timeout_seconds: int = TIMEOUT_DATASET_VALIDATION
    ) -> dict:
        """
        Waits for a Dataset to finish validation.

        This method will return once the validation process is finished. Do check
        the status to ensure that the validation process is *SUCCEEDED*.

        This will repeatedly retrieve the Dataset from the DAR service until the
        Dataset is no longer in status **VALIDATING**.

        The timeout in the *timeout_in_seconds* parameter dictates how long the method
        will wait for the validation to finish. Note that this is not a hard guarantee
        on the time it takes to execute this method!
        After the timeout expires, the dataset will be retrieved one last time to
        check the status.

        Returns the API response of the last GET on the Dataset.

        .. note::
            The act of retrieving the dataset can add a significant amount of time to
            the *timeout_in_seconds* due to network latency and service behavior.
            Unless overriden, the underlying HTTP implementation in :class:`.DARSession`
            uses its own timeouts to prevent the HTTP requests from blocking the
            entire application.

        :param dataset_id: identifier of the dataset
        :param timeout_seconds: how long to wait before giving up
        :return: API response of final GET on dataset
        :raises: DARDatasetInvalidStateException: if dataset in
                 status **NO_DATA** or **UPLOADING**
        :raises: DatasetValidationTimeout: if validation takes longer than
                 *timeout_in_seconds*
        :raises: DatasetValidationFailed: if validation does not finish in state
                **SUCCEEDED**
        """
        polling_class = self.polling_class()
        polling_instance = polling_class(timeout_seconds=timeout_seconds)

        def polling_function() -> dict:
            self.log.info("Polling status on Dataset ID '%s'", dataset_id)
            return self.read_dataset_by_id(dataset_id)

        self.log.info(
            "Waiting for validation of Dataset ID '%s' to succeed!", dataset_id
        )

        try:
            response = polling_instance.poll_until_success(
                polling_function=polling_function,
                success_function=self.is_dataset_validation_finished,
            )
        except PollingTimeoutException as exception:
            msg = "Dataset validation for ID '{}' did not finish in {}s".format(
                dataset_id, timeout_seconds
            )
            self.log.exception(msg)
            new_exception = DatasetValidationTimeout(msg)
            raise new_exception from exception

        if self.is_dataset_validation_failed(response):
            msg = (
                "Validation for Dataset '{}' failed with status '{}' and"
                " validation message: '{}'".format(
                    response["id"], response["status"], response["validationMessage"]
                )
            )
            self.log.error(msg)
            raise DatasetValidationFailed(msg)
        self.log.info(
            "Dataset '%s' has status '%s'.", response["id"], response["status"]
        )
        return response

    def upload_data_and_validate(
        self, dataset_id: str, data_stream: typing.BinaryIO
    ) -> dict:
        """
        Uploads a dataset and waits for validation to finish.

        This is a simple wrapper around :meth:`upload_data_to_dataset` and
        :meth:`wait_for_dataset_validation`. See these methods for possible
        exceptions.

        :param dataset_id: identifier of the dataset
        :param data_stream: a data stream returning bytes
        :return: API response of final GET on Dataset as dict
        """
        # TODO: pass timeout!
        self.upload_data_to_dataset(dataset_id, data_stream=data_stream)
        data_set = self.wait_for_dataset_validation(dataset_id)
        return data_set

    @staticmethod
    def is_dataset_validation_finished(dataset: dict) -> bool:
        """
        Returns True if a Dataset has a final state.

        This does not imply that the Dataset validation is *SUCCEEDED*; it merely
        checks if the process has finished.

        Also see :meth:`is_dataset_validation_failed`.

        :param dataset: Dataset Resource as returned by API
        :return: True if validation process is finished, succesful or not
        :raises: DatasetInvalidStateException if validation has not yet started
        """
        if dataset["status"] in [
            DatasetStatus.NO_DATA.value,
            DatasetStatus.UPLOADING.value,
        ]:
            msg = "Cannot wait for Dataset '{}' in status".format(dataset["id"])
            msg += " '{}'! Upload must finish first.".format(dataset["status"])
            raise DatasetInvalidStateException(msg)
        if dataset["status"] in [
            DatasetStatus.UPLOADING.value,
            DatasetStatus.VALIDATING.value,
        ]:
            return False
        return True

    @staticmethod
    def is_dataset_validation_failed(dataset: dict) -> bool:
        """
        Returns True if a Dataset validation has failed.

        A return value of False does not imply that the Dataset was validated
        successfully. The Deployment is simply in a non-failed state. This can
        also be any non-final state.

        Also see :meth:`is_dataset_validation_finished`.

        :param dataset: Dataset Resource as returned by API
        :return: True if Dataset validation has failed
        """
        if dataset["status"] in [
            DatasetStatus.PROGRAM_ERROR.value,
            DatasetStatus.VALIDATION_FAILED.value,
            DatasetStatus.INVALID_DATA.value,
        ]:
            return True
        return False
