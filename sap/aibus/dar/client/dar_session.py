"""
This module contains the HTTP Transport layer used to interact with the DAR
service.
"""
import typing

import requests
from requests import Response

from sap.aibus.dar.client.exceptions import DARHTTPException
from sap.aibus.dar.client.util.credentials import CredentialsSource
from sap.aibus.dar.client.util.http_transport import (
    TimeoutRetrySession,
    TimeoutPostRetrySession,
    enforce_https_except_localhost,
)


class DARSession:
    """
    A HTTP client for the DAR service.

    This client provides some lower-level primitives to interact
    with the ReST API of the DAR service.

    The client is aware of the base URL of the service and all request
    methods expect the path component to be passed instead of the full URL.

    All requests are authenticated.

    The requests methods return a :py:class:`requests.Response` object. All
    methods can raise a :py:class:`DARHTTPException`. The underlying
    :py:mod:`requests` library may raise
    :py:class:`requests.RequestException`.

    This class internally uses :py:class:`TimeoutRetrySession`.
    """

    def __init__(self, base_url: str, credentials_source: CredentialsSource):
        """
        Constructor.

        Example construction:

        .. doctest:
            >>> from sap.aibus.dar.client.util.credentials import \
                StaticCredentialsSource
            >>> cred_source = StaticCredentialsSource("EXAMPLE TOKEN")
            >>> url = "https://data-attribute-recommendation.x.sap.hana.ondemand.com/"
            >>> DARSession(url, cred_source) # doctest: +ELLIPSIS
            <...DARSession object at 0x...>

        :param base_url: Base URL of the service.
        :param credentials_source: :py:class:`CredentialsSource` used for authentication
        """
        if base_url[-1] == "/":
            # Normalize base url.
            base_url = base_url[:-1]
        enforce_https_except_localhost(base_url)
        self.base_url = base_url
        self.credentials_source = credentials_source
        self.http = TimeoutRetrySession()
        self.http_post_retry = TimeoutPostRetrySession()

    def _get_headers(self):
        return {
            "Authorization": "Bearer " + self.credentials_source.token(),
            "User-Agent": "DAR-SDK requests/" + _get_requests_version(),
            "Accept": "application/json;q=0.9,text/plain",
        }

    def get_from_endpoint(self, endpoint: str) -> Response:
        """
        Performs **GET** request against **endpoint**.

        :param endpoint: Path component of URL
        :return: the :py:class:`requests.Response` object.
        :raise: DARHTTPException
        :raise: RequestException
        """
        url = self.base_url + endpoint

        response = self.http.get(url, headers=self._get_headers())
        self._check_status_code(response, url)

        return response

    def delete_from_endpoint(self, endpoint: str) -> Response:
        """
        Performs **DELETE** request against **endpoint**.

        :param endpoint: Path component of URL
        :return: :py:class:`requests.Response`
        :raise: DARHTTPException
        :raise: RequestException
        """
        url = self.base_url + endpoint
        response = self.http.delete(url, headers=self._get_headers())
        self._check_status_code(response, url)
        return response

    @staticmethod
    def _check_status_code(response, url):
        if response.status_code > 299:
            raise DARHTTPException.create_from_response(url, response)

    def post_to_endpoint(
        self, endpoint: str, payload: dict, retry: bool = False
    ) -> Response:
        """
        Performs **POST** request against **endpoint**.

        The given **payload** is encoded as JSON and sent as the body
        of the request.

        If **retry** is True, the request will be retried in case of errors. This
        includes HTTP error status codes in the response returned by the remote
        API endpoint as well as network issues such as read timeouts or connection
        resets.
        Note that errors occuring before the connection is initially established are
        **always** retried.

        See :ref:`retry` for trade-offs involved here.

        :param endpoint: Path component of URL
        :param payload: Body of the request. Will be encoded to JSON.
        :param retry: whether to retry on failed requests. Defaults to False.
        :return: :py:class:`requests.Response`
        :raise: DARHTTPException
        :raise: RequestException
        """
        url = self.base_url + endpoint
        connection = self.http
        if retry:
            connection = self.http_post_retry
        response = connection.post(url, headers=self._get_headers(), json=payload)
        self._check_status_code(response, url)
        return response

    def post_data_to_endpoint(
        self, endpoint: str, data_stream: typing.BinaryIO
    ) -> Response:
        """
        Performs **POST** request with raw data against **endpoint**.

        The **data_stream** argument must be a :term:`binary file <python:binary file>`
        or a compatible object. Effectively, the **data_stream** should have a
        **read()** method which returns `byte`, not `str`.

        :param endpoint: Path component of URL
        :param data_stream: data to be uploaded as a file-like object
        :return: :py:class:`requests.Response`
        :raise: DARHTTPException
        :raise: RequestException
        """
        url = self.base_url + endpoint
        response = self.http.post(url, headers=self._get_headers(), data=data_stream)
        self._check_status_code(response, url)
        return response

    def post_to_url(self, url: str, payload: dict, retry: bool = False) -> Response:
        """
        Performs **POST** request against fully-qualified URL

        :param url: a fully-qualified inference URL
        :param payload: request body
        :param retry: enables retrying a failed request
        """
        connection = self.http
        if retry:
            connection = self.http_post_retry
        response = connection.post(url, headers=self._get_headers(), json=payload)
        self._check_status_code(response, url)
        return response


def _get_requests_version():
    requests_version = None
    try:
        requests_version = requests.__version__
    except Exception:  # nosec pylint: disable=broad-except
        pass
    if requests_version is None:
        return "Unknown"
    return requests_version
