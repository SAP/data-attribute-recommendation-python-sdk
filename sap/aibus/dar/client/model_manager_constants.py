"""
Constants for the ModelManagerClient.
"""
from enum import Enum


class JobStatus(Enum):
    """
    Possible values for the **status** field of a Job.

    See the section on `Training Job Lifecycle`_ in the official
    DAR documentation.

    .. _Training Job Lifecycle:
        https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/0fc40aa077ce4c708c1e5bfc875aa3be.html
    """

    #: Job has been enqueued.
    PENDING = "PENDING"
    #: Job is now being processed.
    RUNNING = "RUNNING"
    #: Job finished successfully and Model is ready for Deployment.
    SUCCEEDED = "SUCCEEDED"
    #: Training Job failed. Please try again.
    FAILED = "FAILED"


class DeploymentStatus(Enum):
    """
    Possible values for the **status** field of a Deployment.

    See the section on `Deployment Lifecycle`_ in the official
    DAR documentation.

    .. _Deployment Lifecycle:
        https://help.sap.com/viewer/105bcfd88921418e8c29b24a7a402ec3/SHIP/en-US/f473b5b19a3b469e94c40eb27623b4f0.html
    """

    #: status PENDING for a Deployment
    PENDING = "PENDING"
    #: Deployment is successful and theMmodel can now be used for Inference.
    SUCCEEDED = "SUCCEEDED"
    #: Deployment has failed. Delete Deployment and deploy Model again.
    FAILED = "FAILED"
    #: Deployment is stopped (i.e. on trial accounts). Delete Deployment and deploy
    #: Model again.
    STOPPED = "STOPPED"


class ModelManagerPaths:
    """
    Endpoints for the DAR ModelManager microservice.
    """

    #: Path for the ModelTemplate collection
    ENDPOINT_MODEL_TEMPLATE_COLLECTION = "/model-manager/api/v3/modelTemplates"

    #: Path for Job collection
    ENDPOINT_JOB_COLLECTION = "/model-manager/api/v3/jobs"

    #: Path for the Model collection
    ENDPOINT_MODEL_COLLECTION = "/model-manager/api/v3/models"

    #: Path for the Deployment collection
    ENDPOINT_DEPLOYMENT_COLLECTION = "/model-manager/api/v3/deployments"

    #: Path for the BusinessBlueprint collection
    ENDPOINT_BUSINESS_BLUEPRINT_TEMPLATE_COLLECTION = (
        "/model-manager/api/v3/businessBlueprints"
    )

    @classmethod
    def format_model_templates_endpoint_by_id(cls, model_template_id: str) -> str:
        # How can I fix the formatting of the doctest below without introducing a lot
        # of whitespace in the rendered documentation?
        """
        Returns the path of a ModelTemplate with given identifier.

        .. doctest::

            >>> ModelManagerPaths.format_model_templates_endpoint_by_id(\
'd7810207-ca31-4d4d-9b5a-841a644fd81f')
            '/model-manager/api/v3/modelTemplates/d7810207-ca31-4d4d-9b5a-841a644fd81f'

        :param model_template_id: identifier of ModelTemplate
        :return: endpoint, to be used as URL component
        """
        return cls.ENDPOINT_MODEL_TEMPLATE_COLLECTION + "/" + model_template_id

    @classmethod
    def format_job_endpoint_by_id(cls, job_id: str) -> str:
        """
        Returns the path of a Job with given identifier.

        .. doctest::

            >>> ModelManagerPaths.format_job_endpoint_by_id(\
            '222936e3-0350-4cd2-903d-67cb712b6af6')
            '/model-manager/api/v3/jobs/222936e3-0350-4cd2-903d-67cb712b6af6'

        :param job_id: identifier of job
        :return: endpoint, to be used as URL component
        """
        return cls.ENDPOINT_JOB_COLLECTION + "/" + job_id

    @classmethod
    def format_model_endpoint_by_name(cls, model_name: str):
        """
        Returns the path of a Model with given name.

        .. doctest::

            >>> ModelManagerPaths.format_model_endpoint_by_name('my-model')
            '/model-manager/api/v3/models/my-model'

        :param model_name: name of the Model
        :return: endpoint, to be used as URL component
        """
        return cls.ENDPOINT_MODEL_COLLECTION + "/" + model_name

    @classmethod
    def format_deployment_endpoint_by_id(cls, deployment_id: str):
        """
        Returns the path of a Deployment with given name.

        .. doctest::

            >>> ModelManagerPaths.format_deployment_endpoint_by_id(\
                'c45928f5-179c-451e-ae0d-ea33c26391ea')
            '/model-manager/api/v3/deployments/c45928f5-179c-451e-ae0d-ea33c26391ea'

        :param deployment_id: name of the Model
        :return: endpoint, to be used as URL component
        """
        return cls.ENDPOINT_DEPLOYMENT_COLLECTION + "/" + deployment_id

    @classmethod
    def format_business_blueprint_endpoint_by_id(
        cls, business_blueprint_id: str
    ) -> str:
        """
        Returns the path of a BusinessBlueprintTemplate with given identifier.

        .. doctest::

            >>> ModelManagerPaths.format_business_blueprint_endpoint_by_id(\
'4788254b-0bad-4757-a67f-92d5b55f322d')
            '/model-manager/api/v3/businessBlueprints/4788254b-0bad-4757-a67f-92d5b55f322d'

        :param business_blueprint_id: identifier of BusinessBlueprintTemplate
        :return: endpoint, to be used as URL component
        """
        return (
            cls.ENDPOINT_BUSINESS_BLUEPRINT_TEMPLATE_COLLECTION
            + "/"
            + business_blueprint_id
        )
