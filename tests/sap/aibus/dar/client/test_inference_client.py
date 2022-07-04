# type: ignore[assignment]
# The pragma above causes mypy to ignore this file:
# mypy cannot deal with some of the monkey-patching we do below.
# https://github.com/python/mypy/issues/2427
from typing import Optional
from unittest.mock import call, Mock

import pytest
from requests import RequestException, Timeout

from sap.aibus.dar.client.exceptions import DARHTTPException, InvalidWorkerCount
from sap.aibus.dar.client.inference_client import InferenceClient
from tests.sap.aibus.dar.client.test_data_manager_client import (
    AbstractDARClientConstruction,
    prepare_client,
)
from tests.sap.aibus.dar.client.test_exceptions import create_mock_response_404


class TestInferenceClientConstruction(AbstractDARClientConstruction):
    clazz = InferenceClient


DAR_URL = "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/"


@pytest.fixture()
def inference_client():
    return prepare_client(DAR_URL, InferenceClient)


class TestInferenceClient:
    def objects(
        self, object_id: Optional[str] = "b5cbcb34-7ab9-4da5-b7ec-654c90757eb9"
    ):
        """
        Returns sample Objects used as classification inputs.
        """
        return [
            {
                "objectId": object_id,
                "features": [{"name": "manufacturer", "value": "ACME"}],
            }
        ]

    @staticmethod
    def inference_response(
        prediction_count,
        object_id: Optional[str] = "b5cbcb34-7ab9-4da5-b7ec-654c90757eb9",
    ):
        """
        Returns a sample InferenceResponseSchema with the given number of
        predictions.
        """
        return {
            "id": "8ba8d237-7625-4986-8b31-ab5dca5cdd80",
            "status": "DONE",
            "processedTime": "2018-08-31T11:45:54.727934+00:00",
            "predictions": [
                {
                    "objectId": object_id,
                    "labels": [{"name": "category", "value": "ANVIL"}],
                }
                for _ in range(prediction_count)
            ],
        }

    def test_create_inference_request(self, inference_client: InferenceClient):
        """
        Checks inference call.
        """
        response = inference_client.create_inference_request(
            "my-model", objects=self.objects()
        )

        expected_call = call(
            "/inference/api/v3/models/my-model/versions/1",
            payload={"topN": 1, "objects": self.objects()},
            retry=True,
        )

        assert inference_client.session.post_to_endpoint.call_args_list == [
            expected_call
        ]

        assert (
            inference_client.session.post_to_endpoint.return_value.json.return_value
            == response
        )

    def test_create_inference_request_with_top_n(
        self, inference_client: InferenceClient
    ):
        """
        Checks if top_n parameter is passed correctly.
        """
        response = inference_client.create_inference_request(
            "a-test-model", objects=self.objects(), top_n=99, retry=False
        )
        expected_call = call(
            "/inference/api/v3/models/a-test-model/versions/1",
            payload={"topN": 99, "objects": self.objects()},
            retry=False,
        )

        assert inference_client.session.post_to_endpoint.call_args_list == [
            expected_call
        ]

        assert (
            inference_client.session.post_to_endpoint.return_value.json.return_value
            == response
        )

    def test_create_inference_request_with_retry_enabled(
        self, inference_client: InferenceClient
    ):
        """
        Checks if retry parameter is passsed correctly.
        """
        response = inference_client.create_inference_request(
            "my-model", objects=self.objects(), retry=True
        )

        expected_call = call(
            "/inference/api/v3/models/my-model/versions/1",
            payload={"topN": 1, "objects": self.objects()},
            retry=True,
        )

        assert inference_client.session.post_to_endpoint.call_args_list == [
            expected_call
        ]

        assert (
            inference_client.session.post_to_endpoint.return_value.json.return_value
            == response
        )

    def test_bulk_inference_retry_disabled(self, inference_client: InferenceClient):
        """
        Tests bulk_inference method.

        We expect that larger inference requests are splitted into packages of 50
        objects and that the result is returned as a single list.
        """
        self._assert_bulk_inference_works(inference_client, retry_flag=False)

    def test_bulk_inference_retry_enabled(self, inference_client: InferenceClient):
        """
        Tests if bulk_inference passes the retry flag correctly.
        """
        self._assert_bulk_inference_works(inference_client, retry_flag=True)

    def test_bulk_inference_retry_default(self, inference_client: InferenceClient):
        """
        Tests if bulk_inference defaults its retry parameter to False.
        """
        self._assert_bulk_inference_works(inference_client, retry_flag="default")

    def _assert_bulk_inference_works(
        self, inference_client: InferenceClient, retry_flag
    ):
        # if retry_flag parameter is set to "default", the retry parameter will not
        # passed to InferenceClient.do_bulk_inference - the default is assumed to be
        # False and the internal calls to Inference.create_inference_request will
        # be checked for this.
        many_objects = [self.objects()[0] for _ in range(75)]
        assert len(many_objects) == 75

        # On first call, return response with 50 predictions. On second call,
        # return 25.
        inference_client.session.post_to_endpoint.return_value.json.side_effect = [
            self.inference_response(50),
            self.inference_response(25),
        ]

        retry_kwarg = {}
        if retry_flag != "default":
            retry_kwarg["retry"] = retry_flag

        response = inference_client.do_bulk_inference(
            model_name="test-model",
            objects=many_objects,
            top_n=4,
            worker_count=1,  # Disable concurrency to make tests deterministic.
            **retry_kwarg,
        )

        # The return value is the concatenation of all 'predictions' of the individual
        # inference calls
        assert response == self.inference_response(75)["predictions"]

        expected_retry_flag = retry_flag
        if expected_retry_flag == "default":
            expected_retry_flag = True

        # For 75 objects, we expect two calls.
        expected_calls_to_post = [
            call(
                "/inference/api/v3/models/test-model/versions/1",
                payload={"topN": 4, "objects": many_objects[0:50]},
                retry=expected_retry_flag,
            ),
            call(
                "/inference/api/v3/models/test-model/versions/1",
                payload={"topN": 4, "objects": many_objects[50:75]},
                retry=expected_retry_flag,
            ),
        ]

        assert (
            inference_client.session.post_to_endpoint.call_args_list
            == expected_calls_to_post
        )

    def test_create_inference_with_url_works(self, inference_client: InferenceClient):
        """
        Checks inference call.
        """
        url = DAR_URL + "inference/api/v3/models/my-model/versions/1"
        response = inference_client.create_inference_request_with_url(
            url, objects=self.objects()
        )

        expected_call = call(
            url,
            payload={"topN": 1, "objects": self.objects()},
            retry=True,
        )

        assert inference_client.session.post_to_url.call_args_list == [expected_call]

        assert (
            inference_client.session.post_to_url.return_value.json.return_value
            == response
        )

    def test_create_inference_request_with_url_retry_enabled(
        self, inference_client: InferenceClient
    ):
        """
        Checks if retry parameter is passed correctly.
        """
        url = DAR_URL + "inference/api/v3/models/my-model/versions/1"

        response = inference_client.create_inference_request_with_url(
            url=url, objects=self.objects(), retry=True
        )

        expected_call = call(
            url,
            payload={"topN": 1, "objects": self.objects()},
            retry=True,
        )

        assert inference_client.session.post_to_url.call_args_list == [expected_call]

        assert (
            inference_client.session.post_to_url.return_value.json.return_value
            == response
        )

    def test_bulk_inference_error(self, inference_client: InferenceClient):
        """
        Tests if do_bulk_inference method will recover from errors.
        """

        response_404 = create_mock_response_404()
        url = "http://localhost:4321/test/"

        exception_404 = DARHTTPException.create_from_response(url, response_404)

        # The old trick to return different values in a Mock based on the call order
        # does not work here because the code is concurrent. Instead, we use a different
        # objectId for those objects where we want the request to fail
        def make_mock_post(exc):
            def post_to_endpoint(*args, **kwargs):
                payload = kwargs.pop("payload")
                object_id = payload["objects"][0]["objectId"]
                if object_id == "expected-to-fail":
                    raise exc
                elif object_id == "b5cbcb34-7ab9-4da5-b7ec-654c90757eb9":
                    response = Mock()
                    response.json.return_value = self.inference_response(
                        len(payload["objects"])
                    )
                    return response
                else:
                    raise ValueError("objectId '%s' not handled in test." % object_id)

            return post_to_endpoint

        # Try different exceptions
        exceptions = [
            exception_404,
            RequestException("Request Error"),
            Timeout("Timeout"),
        ]
        for exc in exceptions:
            inference_client.session.post_to_endpoint.side_effect = make_mock_post(exc)

            many_objects = []
            many_objects.extend([self.objects()[0] for _ in range(50)])
            many_objects.extend(
                [self.objects(object_id="expected-to-fail")[0] for _ in range(50)]
            )
            many_objects.extend([self.objects()[0] for _ in range(40)])
            assert len(many_objects) == 50 + 50 + 40

            response = inference_client.do_bulk_inference(
                model_name="test-model",
                objects=many_objects,
                top_n=4,
            )

            expected_error_response = {
                "objectId": "expected-to-fail",
                "labels": None,
                # If this test fails, I found it can make pytest/PyCharm hang because it
                # takes too much time in difflib.
                "_sdk_error": "{}: {}".format(exc.__class__.__name__, str(exc)),
            }

            expected_response = []
            expected_response.extend(self.inference_response(50)["predictions"])
            expected_response.extend(expected_error_response for _ in range(50))
            expected_response.extend(self.inference_response(40)["predictions"])

            assert len(response) == len(expected_response)
            assert response == expected_response

    def test_bulk_inference_error_no_object_ids(
        self, inference_client: InferenceClient
    ):
        response_404 = create_mock_response_404()
        url = "http://localhost:4321/test/"

        exception_404 = DARHTTPException.create_from_response(url, response_404)

        inference_client.session.post_to_endpoint.return_value.json.side_effect = [
            self.inference_response(50, object_id=None),
            exception_404,
            self.inference_response(22, object_id=None),
        ]

        inference_objects = [
            self.objects(object_id=None)[0] for _ in range(50 + 50 + 22)
        ]

        response = inference_client.do_bulk_inference(
            model_name="test-model",
            objects=inference_objects,
            top_n=4,
            worker_count=1,  # disable concurrency to make tests deterministic
        )
        expected_error_response = {
            "objectId": None,
            "labels": None,
            # If this test fails, I found it can make pytest/PyCharm hang because it
            # takes too much time in difflib.
            "_sdk_error": "{}: {}".format(
                exception_404.__class__.__name__, str(exception_404)
            ),
        }
        expected_response = []
        expected_response.extend(
            self.inference_response(50, object_id=None)["predictions"]
        )
        expected_response.extend(expected_error_response for _ in range(50))
        expected_response.extend(
            self.inference_response(22, object_id=None)["predictions"]
        )

        assert response == expected_response

    def test_worker_count_validation(self, inference_client: InferenceClient):

        many_objects = [self.objects()[0] for _ in range(75)]

        with pytest.raises(InvalidWorkerCount) as context:
            inference_client.do_bulk_inference(
                model_name="test-model", objects=many_objects, worker_count=5
            )
        assert "worker_count too high: 5. Up to 4 allowed." in str(context.value)

        with pytest.raises(InvalidWorkerCount) as context:
            inference_client.do_bulk_inference(
                model_name="test-model", objects=many_objects, worker_count=0
            )
        assert "worker_count must be greater than 0" in str(context.value)

        with pytest.raises(InvalidWorkerCount) as context:
            inference_client.do_bulk_inference(
                model_name="test-model", objects=many_objects, worker_count=-1
            )
        assert "worker_count must be greater than 0" in str(context.value)

        with pytest.raises(InvalidWorkerCount) as context:
            inference_client.do_bulk_inference(
                model_name="test-model",
                objects=many_objects,
                worker_count=None,
            )
            assert "worker_count cannot be None" in str(context.value)
