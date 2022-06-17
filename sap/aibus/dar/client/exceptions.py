"""
All exceptions raised by the DAR client implementation itself.
"""
import json
from collections import OrderedDict
import datetime
from io import StringIO
from typing import Optional

from requests import Response, PreparedRequest


class DARException(Exception):
    """
    General error in the DAR client.

    This is the base exception class for the DAR client. All exceptions raised by the
    client itself inherit from this class.

    Note that other libraries used internally will raise their own exceptions.
    In particular, see :class:`DARSession` for its use of HTTP libraries and their
    exceptions.
    """

    pass


class HTTPSRequired(DARException):
    """
    URLs must use a HTTPS-scheme.
    """

    def __init__(self):
        msg = "URL must use https scheme. Unencrypted connections are not supported."
        super().__init__(msg)


class DARPollingTimeoutException(DARException):
    """
    Operation being polled took too long to finish.
    """

    pass


class DatasetValidationTimeout(DARPollingTimeoutException):
    """
    Dataset took too long to finish its validation process.
    """

    pass


class DatasetValidationFailed(DARException):
    """
    Dataset validation finished with a non-success state.
    """

    pass


class InvalidStateException(DARException):
    """
    A resource was in an unexpected state.
    """

    pass


class DatasetInvalidStateException(InvalidStateException):
    """
    Dataset was in an unexpected state.
    """

    pass


class TrainingJobTimeOut(DARPollingTimeoutException):
    """
    Training took too long to finish.
    """

    pass


class TrainingJobFailed(DARException):
    """
    Training job failed.
    """

    pass


class DeploymentTimeOut(DARPollingTimeoutException):
    """
    Deployment took too long too succeed.
    """

    pass


class DeploymentFailed(DARException):
    """
    Deployment finished with a non-success state.
    """

    pass


class CreateTrainingJobFailed(DARException):
    """
    Create training job failed.
    """

    pass


class JobNotFound(DARException):
    """
    Training job not found
    """

    pass


class InvalidWorkerCount(DARException):
    """
    Invalid worker_count parameter is specified.

    .. versionadded:: 0.12.0
    """


class ModelAlreadyExists(DARException):
    """
    Model already exists and must be deleted first.

    Note that this is not really used by the :class:`ModelManagerClient`, but
    rather by higher-level methods in :class:`ModelCreator` and similar.

    For methods interacting directly with the API, a request which will
    conflict will instead raise a :class:`DARHTTPException` with an appropriate code.
    """

    def __init__(self, model_name: str):
        """
        Constructor.

        :param: model_name: Name of the model which alreadx exists
        """
        msg = "Model '%s' already exists." % model_name
        msg += (
            "To re-use the name, please delete the model"
            " first or choose a different name."
        )
        super().__init__(msg)


class DARHTTPException(DARException):
    """
    Error occured when talking to the DAR service over HTTP.

    This exception exposes many debug-level details which are highly useful
    when investigating a problem with the service.

    Note that this exception will only be used if the server actually sent a response.
    Connection problems can cause the connection to abort before a response is sent.

    When creating a ticket, please include as much information as possible.
    """

    def __init__(self, url: str, response: Response):
        super().__init__()
        self.url = url
        self._response = response
        self.exception_timestamp = datetime.datetime.now(tz=datetime.timezone.utc)

    @property
    def response(self) -> Response:
        """
        The full :class:`requests.Response` object.

        :return: the original API response object
        """
        return self._response

    @property
    def request(self) -> PreparedRequest:
        """
        The full :class:`requests.PreparedRequest` sent to the DAR service.

        :return: the original request object
        """
        return self.response.request

    @property
    def status_code(self) -> int:
        """
        The HTTP status of the response.

        :return: response status code
        """
        return self.response.status_code

    @property
    def response_body(self) -> str:
        """
        Returns response body.

        Is pretty printed if response body is JSON or
        returned as-is otherwise.

        :return: response body as string
        """
        try:
            decoded = self.response.json()
            return json.dumps(decoded, sort_keys=True, indent=4)
        except ValueError:
            return self.response.text

    @property
    def response_reason(self) -> str:
        """
        Returns the reason phrase sent along the status code.

        This can be useful to understand better the reason for
        a given status code sent by the server.

        :return: reason phrase as string
        """
        # request's Response.raise_for_status implementation indicates
        # that the Response.reason can be a bytes object, so we attempt
        # to decode similar to Response.raise_for_status.
        reason = self.response.reason
        if isinstance(reason, str):
            return reason
        try:
            return reason.decode("utf-8")
        except UnicodeDecodeError:
            return reason.decode("iso-8859-1")

    @property
    def correlation_id(self) -> Optional[str]:
        """
        The correlation ID, if sent by the server.

        The correlation ID is a technical identifier for individual requests
        and useful when investigating any problems encountered while processing
        a request.

        :return: correlation ID
        """
        return self.response.headers.get("X-Correlation-Id")

    @property
    def vcap_request_id(self) -> Optional[str]:
        """
        The VCAP request ID, if sent by the server.

        The VCAP request ID is a technical identifier for individual requests
        and useful when investigating any problems encountered while processing
        a request.

        :return: VCAP request ID
        """
        return self.response.headers.get("X-Vcap-Request-Id")

    @property
    def server_header(self) -> Optional[str]:
        """
        Value of the *SERVER* HTTP header, if sent by the server.

        :return: SERVER HTTP header.
        """
        return self.response.headers.get("Server")

    @property
    def cf_router_error(self) -> Optional[str]:
        """
        Value of the *X-CF-RouteError* header, if sent by the server.

        :return: *X-CF-RouteError* HTTP header.
        """
        return self.response.headers.get("X-Cf-Routererror")

    @classmethod
    def create_from_response(cls, url: str, response: Response):
        """
        Factory method to create exception from a server response.

        :param url: URL of the request
        :param response: response sent by the server
        :return: the exception object
        """
        return cls(url=url, response=response)

    @property
    def debug_message(self):
        """
        Returns a debug message with useful details on request and response.

        :return: details on request and response
        """
        debug_data = self._get_debug_data()

        debug_str = StringIO()
        for key, val in debug_data.items():
            debug_str.write(key)
            debug_str.write(": ")
            debug_str.write("'%s'" % val)
            debug_str.write("\n")
        return debug_str.getvalue()

    def _get_debug_data(self):
        debug_data = OrderedDict()
        debug_data["URL"] = self.url
        debug_data["Method"] = self.request.method
        debug_data["Status Code"] = self.status_code
        debug_data["Status Reason"] = self.response_reason
        debug_data["Response Body"] = self.response_body
        debug_data["Correlation ID"] = self.correlation_id
        debug_data["VCAP Request ID"] = self.vcap_request_id
        debug_data["CF Router Error"] = self.cf_router_error
        debug_data["Server Header"] = self.server_header
        debug_data["Exception Timestamp"] = self.exception_timestamp.isoformat()
        return debug_data

    def __str__(self):
        """
        All debug details contained in this exception.

        :return: all details
        """
        return self.__class__.__name__ + "\n" + self.debug_message
