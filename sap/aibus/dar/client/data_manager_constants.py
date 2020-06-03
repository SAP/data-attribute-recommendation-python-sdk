"""
Constants for the DataManagerClient.
"""
from enum import Enum


class DatasetStatus(Enum):
    """
    Possible values for the **status** field of a Dataset.

    See the section on `Dataset Lifecycle`_ in the official
    DAR documentation.

    .. _Dataset Lifecycle:
        https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/a9b7429687a04e769dbc7955c6c44265.html
    """

    #: No data has been uploaded yet.
    NO_DATA = "NO_DATA"
    #: Data is currently being uploaded.
    UPLOADING = "UPLOADING"
    #: Validation is in process.
    VALIDATING = "VALIDATING"
    #: Uploaded data is invalid, i.e. not a CSV or does not match DatasetSchema.
    INVALID_DATA = "INVALID_DATA"
    #: Internal Server Error occured during validation. Create a new Dataset.
    VALIDATION_FAILED = "VALIDATION_FAILED"
    #: Internal Server Error occured during validation. Create a new Dataset.
    PROGRAM_ERROR = "PROGRAM_ERROR"
    #: Validation finished successfully. The Dataset may be used for training.
    SUCCEEDED = "SUCCEEDED"


class DataManagerPaths:
    """
    Endpoints for the DAR DataManager microservice.
    """

    #: Path for the DatasetSchema collection
    ENDPOINT_DATASET_SCHEMA_COLLECTION = "/data-manager/api/v3/datasetSchemas"

    #: Path for the Dataset collection
    ENDPOINT_DATASET_COLLECTION = "/data-manager/api/v3/datasets"

    @staticmethod
    def format_dataset_schemas_endpoint_by_id(identifier: str) -> str:
        """
        Returns the path of a DatasetSchema with given identifier.

        >>> DataManagerPaths.format_dataset_schemas_endpoint_by_id(\
            '9ac12220-b0b2-45ec-a81b-5dd5ca6536e9')
        '/data-manager/api/v3/datasetSchemas/9ac12220-b0b2-45ec-a81b-5dd5ca6536e9'

        :param identifier: ID of DatasetSchema
        :return: endpoint path component
        """
        endpoint = "/data-manager/api/v3/datasetSchemas/{}".format(identifier)
        return endpoint

    @staticmethod
    def format_dataset_endpoint_by_id(identifier: str) -> str:
        """
        Returns the path of a Dataset with given identifier.

        >>> DataManagerPaths.format_dataset_endpoint_by_id(\
            '9678dcdd-239e-4dfc-8795-5924152c97a3')
        '/data-manager/api/v3/datasets/9678dcdd-239e-4dfc-8795-5924152c97a3'


        :param identifier: ID of Dataset
        :return: endpoint path component
        """
        endpoint = "/data-manager/api/v3/datasets/{}".format(identifier)
        return endpoint

    @classmethod
    def format_data_endpoint_by_id(cls, identifier: str) -> str:
        """
        Returns the path of the upload endpoint for a Dataset with given identifier.

        >>> DataManagerPaths.format_data_endpoint_by_id(\
            'd862fcba-06b1-4eaa-93c1-a0b5980938f5')
        '/data-manager/api/v3/datasets/d862fcba-06b1-4eaa-93c1-a0b5980938f5/data'

        :param identifier: ID of Dataset
        :return: endpoint path component
        """
        dataset_endpoint = cls.format_dataset_endpoint_by_id(identifier)
        return dataset_endpoint + "/data"
