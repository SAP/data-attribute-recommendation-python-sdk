"""
Client API for the Inference microservice.
"""
from typing import List

from sap.aibus.dar.client.base_client import BaseClientWithSession
from sap.aibus.dar.client.inference_constants import InferencePaths
from sap.aibus.dar.client.util.lists import split_list

#: How many objects can be processed per inference request
LIMIT_OBJECTS_PER_CALL = 50

#: How many labels to predict for a single object by default
TOP_N = 1


class InferenceClient(BaseClientWithSession):
    """
    A client for the DAR Inference microservice.

    This class implements all basic API calls as well as some convenience methods
    which wrap individual API calls.

    If the API call fails, all methods will raise an :exc:`DARHTTPException`.
    """

    def create_inference_request(
        self,
        model_name: str,
        objects: List[dict],
        top_n: int = TOP_N,
        retry: bool = False,
    ) -> dict:
        """
        Performs inference for the given *objects* with *model_name*.

        For each object in *objects*, returns the *topN* best predictions.

        The *retry* parameter determines whether to retry on HTTP errors indicated by
        the remote API endpoint or for other connection problems. See :ref:`retry` for
        trade-offs involved here.

        .. note::

            This endpoint called by this method has a limit of *LIMIT_OBJECTS_PER_CALL*
            on the number of *objects*. See :meth:`do_bulk_inference` to circumvent
            this limit.

        :param model_name: name of the model used for inference
        :param objects: Objects to be classified
        :param top_n: How many predictions to return per object
        :param retry: whether to retry on errors. Default: False
        :return: API response
        """
        self.log.debug(
            "Submitting Inference request for model '%s' with '%s'"
            " objects and top_n '%s' ",
            model_name,
            len(objects),
            top_n,
        )
        endpoint = InferencePaths.format_inference_endpoint_by_name(model_name)
        response = self.session.post_to_endpoint(
            endpoint, payload={"topN": top_n, "objects": objects}, retry=retry
        )
        as_json = response.json()
        self.log.debug("Inference response ID: %s", as_json["id"])
        return as_json

    def do_bulk_inference(
        self,
        model_name: str,
        objects: List[dict],
        top_n: int = TOP_N,
        retry: bool = True,
    ) -> List[dict]:
        """
        Performs bulk inference for larger collections.

        For *objects* collections larger than *LIMIT_OBJECTS_PER_CALL*, splits
        the data into several smaller Inference requests.

        Returns the aggregated values of the *predictions* of the original API response
        as returned by :meth:`create_inference_request`.

        .. note::

            This method calls the inference endpoint multiple times to process all data.
            For non-trial service instances, each call will incur a cost.

            If one of the calls fails, this method will raise an Exception and the
            progress will be lost. In this case, all calls until the Exception happened
            will be charged.

            To reduce the likelihood of a failed request terminating the bulk inference
            process, this method will retry failed requests.

            There is a small chance that even retried requests will be charged, e.g.
            if a problem occurs with the request on the client side outside of the
            control of the service and after the service has processed the request.
            To disable `retry` behavior simply pass `retry=False` to the method.

            Typically, the default behavior of `retry=True` is safe and improves
            reliability of bulk inference greatly.

        .. versionchanged:: 0.7.0
            The default for the `retry` parameter changed from `retry=False` to
            `retry=True` for increased reliability in day-to-day operations.


        :param model_name: name of the model used for inference
        :param objects: Objects to be classified
        :param top_n: How many predictions to return per object
        :param retry: whether to retry on errors. Default: True
        :return: the aggregated ObjectPrediction dictionaries
        """
        result = []  # type: List[dict]
        for work_package in split_list(objects, LIMIT_OBJECTS_PER_CALL):
            response = self.create_inference_request(
                model_name, work_package, top_n=top_n, retry=retry
            )
            result.extend(response["predictions"])
        return result
