"""
Client API for the Inference microservice.
"""
from concurrent.futures import ThreadPoolExecutor
from typing import List, Union

from requests import RequestException

from sap.aibus.dar.client.base_client import BaseClientWithSession
from sap.aibus.dar.client.exceptions import DARHTTPException, InvalidWorkerCount
from sap.aibus.dar.client.inference_constants import InferencePaths
from sap.aibus.dar.client.util.lists import split_list

#: How many objects can be processed per inference request
LIMIT_OBJECTS_PER_CALL = 50

#: How many labels to predict for a single object by default
TOP_N = 1

# pylint: disable=too-many-arguments


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
        retry: bool = True,
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

        .. versionchanged:: 0.13.0
           The *retry* parameter now defaults to true. This increases reliability of the
           call. See corresponding note on :meth:`do_bulk_inference`.

        :param model_name: name of the model used for inference
        :param objects: Objects to be classified
        :param top_n: How many predictions to return per object
        :param retry: whether to retry on errors. Default: True
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
        worker_count: int = 4,
    ) -> List[Union[dict, None]]:
        """
        Performs bulk inference for larger collections.

        For *objects* collections larger than *LIMIT_OBJECTS_PER_CALL*, splits
        the data into several smaller Inference requests.

        Requests are executed in parallel.

        Returns the aggregated values of the *predictions* of the original API response
        as returned by :meth:`create_inference_request`. If one of the inference
        requests to the service fails, an artificial prediction object is inserted with
        the `labels` key set to `None` for each of the objects in the failing request.

        Example of a prediction object which indicates an error:

        .. code-block:: python

            {
                'objectId': 'b5cbcb34-7ab9-4da5-b7ec-654c90757eb9',
                'labels': None,
                '_sdk_error': 'RequestException: Request Error'
            }

        In case the `objects` passed to this method do not contain the `objectId` field,
        the value is set to `None` in the error prediction object:

        .. code-block:: python

            {
                'objectId': None,
                'labels': None,
                '_sdk_error': 'RequestException: Request Error'
            }


        .. note::

            This method calls the inference endpoint multiple times to process all data.
            For non-trial service instances, each call will incur a cost.

            To reduce the impact of a failed request, this method will retry failed
            requests.

            There is a small chance that even retried requests will be charged, e.g.
            if a problem occurs with the request on the client side outside the
            control of the service and after the service has processed the request.
            To disable `retry` behavior simply pass `retry=False` to the method.

            Typically, the default behavior of `retry=True` is safe and improves
            reliability of bulk inference greatly.

        .. versionchanged:: 0.7.0
            The default for the `retry` parameter changed from `retry=False` to
            `retry=True` for increased reliability in day-to-day operations.

        .. versionchanged:: 0.12.0
           Requests are now executed in parallel with up to four threads.

           Errors are now handled in this method instead of raising an exception and
           discarding inference results from previous requests. For objects where the
           inference request did not succeed, a replacement `dict` object is placed in
           the returned `list`.
           This `dict` follows the format of the `ObjectPrediction` object sent by the
           service. To indicate that this is a client-side generated placeholder, the
           `labels` key for all ObjectPrediction dicts of the failed inference request
           has value `None`.
           A `_sdk_error` key is added with the Exception details.

        .. versionadded:: 0.12.0
           The `worker_count` parameter allows to fine-tune the number of concurrent
           request threads. Set `worker_count` to `1` to disable concurrent execution of
           requests.


        :param model_name: name of the model used for inference
        :param objects: Objects to be classified
        :param top_n: How many predictions to return per object
        :param retry: whether to retry on errors. Default: True
        :param worker_count: maximum number of concurrent requests
        :raises: InvalidWorkerCount if worker_count param is incorrect
        :return: the aggregated ObjectPrediction dictionaries
        """

        if worker_count is None:
            raise InvalidWorkerCount("worker_count cannot be None!")

        if worker_count > 4:
            msg = "worker_count too high: %s. Up to 4 allowed." % worker_count
            raise InvalidWorkerCount(msg)

        if worker_count <= 0:
            msg = "worker_count must be greater than 0!"
            raise InvalidWorkerCount(msg)

        def predict_call(work_package):
            try:
                response = self.create_inference_request(
                    model_name, work_package, top_n=top_n, retry=retry
                )
                return response["predictions"]
            except (DARHTTPException, RequestException) as exc:
                self.log.warning(
                    "Caught %s during bulk inference. "
                    "Setting results to None for this batch!",
                    exc,
                    exc_info=True,
                )

                prediction_error = [
                    {
                        "objectId": inference_object.get("objectId", None),
                        "labels": None,
                        "_sdk_error": "{}: {}".format(exc.__class__.__name__, str(exc)),
                    }
                    for inference_object in work_package
                ]
                return prediction_error

        results = []

        with ThreadPoolExecutor(max_workers=worker_count) as pool:
            results_iterator = pool.map(
                predict_call, split_list(objects, LIMIT_OBJECTS_PER_CALL)
            )

            for predictions in results_iterator:
                results.extend(predictions)

        return results

    def create_inference_request_with_url(
        self,
        url: str,
        objects: List[dict],
        top_n: int = TOP_N,
        retry: bool = True,
    ) -> dict:
        """
        Performs inference for the given *objects* against fully-qualified URL.
        A complete inference URL can be the passed to the method inference, instead
        of constructing URL from using base url and model name

        .. versionchanged:: 0.13.0
           The *retry* parameter now defaults to true. This increases reliability of the
           call. See corresponding note on :meth:`do_bulk_inference`.

        :param url: fully-qualified inference URL
        :param objects: Objects to be classified
        :param top_n: How many predictions to return per object
        :param retry: whether to retry on errors. Default: True
        :return: API response
        """
        self.log.debug(
            "Submitting Inference request with '%s'"
            " objects and top_n '%s' to url %s",
            len(objects),
            top_n,
            url,
        )
        response = self.session.post_to_url(
            url, payload={"topN": top_n, "objects": objects}, retry=retry
        )
        as_json = response.json()
        self.log.debug("Inference response ID: %s", as_json["id"])
        return as_json
