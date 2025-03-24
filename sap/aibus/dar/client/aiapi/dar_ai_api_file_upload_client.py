"""Client for DAR File Upload AI API."""

import urllib.parse
from typing import Any, Callable

import requests
from requests import Response


class DARAIAPIFileUploadClient:
    """Client for DAR File Upload AI API.

    This client provides methods to upload and delete files on the DAR service,
    handling authentication and request preparation internally.
    """

    def __init__(self, base_url: str, get_token: Callable[[], str]):
        """Initialize the DARFileUploadAIAPIClient.

        :param base_url: The base URL of the DAR AI API.
        :param get_token: A callable to fetch the authorization token.
        """
        self.base_url = base_url + "/files"
        self.get_token = get_token

    def delete_file(self, remote_path: str) -> Response:
        """Delete file under defined remote path.

        :param remote_path: The path to the file to delete on the server.

        :returns: The HTTP response object from the API call.
        """
        url = self.base_url + remote_path

        return self._send("DELETE", url)

    def put_file(
        self, local_path: str, remote_path: str, overwrite: bool = False
    ) -> Response:
        """Upload file to the defined remote path.

        :param local_path: The local path of the file to upload.
        :param remote_path: The destination path for the file on the server.
        :param overwrite: Whether to overwrite the file if it already exists,
                              defaults to False.

        :returns: The HTTP response object from the API call.
        """
        url = self.base_url + remote_path
        headers = {
            # Content-Type MUST be application/octet-stream, even when uploading
            # e.g. CSV files
            "Content-Type": "application/octet-stream",
        }
        params = {"overwrite": overwrite}
        with open(local_path, "rb") as file:
            return self._send(
                method="PUT", url=url, headers=headers, params=params, data=file
            )

    def get_file_from_url(self, url: str) -> Response:
        """Download file under defined url.

        :param url: The url to the file that needs to be downloaded

        :returns: The downloaded file on the server from the url.
        """
        return self._send("GET", url)

    def _send(  # pylint: disable=too-many-arguments
        self,
        method: str,
        url: str,
        headers: dict = None,
        data: Any = None,
        params: dict = None,
    ) -> Response:
        """Send an HTTP request using the `requests` library.

        :param method: The HTTP method (e.g., 'GET', 'POST', 'PUT', 'DELETE').
        :param url: The full URL for the request.
        :param headers: The headers for the request,defaults to None.
        :param data: The data payload for the request (e.g., file data),
                     defaults to None.
        :param params: The query parameters for the URL,defaults to None.

        :returns: The HTTP response object from the API call.
        """
        session = requests.Session()
        auth_headers = {
            "Authorization": self.get_token(),
        }
        if headers:
            auth_headers.update(headers)

        req = requests.Request(
            method=method, url=url, headers=auth_headers, data=data, params=params
        )
        prep = req.prepare()
        prep.url = url
        if params:
            prep.url += "?" + urllib.parse.urlencode(params)
        response = session.send(prep, verify=True)
        return response
