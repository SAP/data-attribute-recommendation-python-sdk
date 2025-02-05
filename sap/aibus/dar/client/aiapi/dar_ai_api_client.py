"""Base client for DAR AI API."""

from typing import Callable
from typing import Optional

from ai_api_client_sdk.ai_api_v2_client import AIAPIV2Client
from sap.aibus.dar.client.aiapi.dar_ai_api_file_upload_client import (
    DARAIAPIFileUploadClient,
)


class DARAIAPIClient(AIAPIV2Client):
    """Base client for DAR AI API."""

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        base_url: str,
        auth_url: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        cert_str: Optional[str] = None,
        key_str: Optional[str] = None,
        cert_file_path: Optional[str] = None,
        key_file_path: Optional[str] = None,
        token_creator: Optional[Callable[[], str]] = None,
    ):
        """
        Initialize the DARAIAPIClient.

        :param base_url: The base URL of the DAR AI API.
        :param auth_url: The URL of the authorization endpoint, defaults to None
        :param client_id: The client id to be used for authorization,
                          defaults to None
        :param client_secret: The client secret to be used for authorization,
                              defaults to None
        :param cert_str: The certificate file content, needs to be provided alongside
                         the key_str parameter, defaults to None
        :param key_str: The key file content, needs to be provided alongside
                        the cert_str parameter, defaults to None
        :param cert_file_path: The path to the certificate file, needs to be provided
                               alongside the key_file_path parameter, defaults to None
        :param key_file_path: The path to the key file, needs to be provided alongside
                              the cert_file_path parameter, defaults to None
        :param token_creator: The function which returns the Bearer token,
                              when called, defaults to None.
        """
        super().__init__(
            base_url=base_url,
            auth_url=auth_url,
            client_id=client_id,
            client_secret=client_secret,
            cert_str=cert_str,
            key_str=key_str,
            cert_file_path=cert_file_path,
            key_file_path=key_file_path,
            token_creator=token_creator,
        )

        self.file_upload_client = DARAIAPIFileUploadClient(
            base_url=base_url, get_token=self.rest_client.get_token
        )
