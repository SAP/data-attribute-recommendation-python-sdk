"""
Constants for the InferenceClient.
"""


class InferencePaths:
    """
    Endpoints for the DAR Inference microservice.
    """

    @staticmethod
    def format_inference_endpoint_by_name(model_name: str):
        """
        Returns the path of an InferenceRequest for the given *model_name*.

        .. doctest::

            >>> InferencePaths.format_inference_endpoint_by_name("test-model")
            '/inference/api/v3/models/test-model/versions/1'


        :param model_name: name of the model
        :return: endpoint, to be used as URL component
        """
        return "/inference/api/v3/models/{}/versions/1".format(model_name)
