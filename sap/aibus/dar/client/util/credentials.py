"""
This module is concerned with retrieval of access tokens for the DAR service.

The code here is a low-level detail and should rarely be used by regular users. Instead,
refer to the higher-level API.
"""

import time
from typing import Callable

from sap.aibus.dar.client.util.http_transport import (
    HttpMethodsProtocol,
    TimeoutRetrySession,
    enforce_https_except_localhost,
)
from sap.aibus.dar.client.util.logging import LoggerMixin


class CredentialsSource:
    """
    Abstract BaseCredentialsSource base class.
    """

    def token(self) -> str:
        """
        Returns an access token for the DAR service.

        Must be implemented by subclasses.

        :return: the token as string
        """
        raise NotImplementedError


class StaticCredentialsSource(CredentialsSource):
    """
    CredentialsSource which is configured with a single token.

    This class is mainly useful for compatibility. It allows the use of tokens obtained
    by some other means or where no credentials are known.
    """

    def __init__(self, token: str):
        """
        Constructor.

        :param token: an existing DAR access token
        """
        self._token = token

    def token(self):
        """
        Returns the DAR access token given during object construction.

        :return: pre-configured DAR access token
        """
        return self._token


class OnlineCredentialsSource(CredentialsSource, LoggerMixin):
    """
    Retrieves a token from the authentication server.

    The token will be cached internally for the validity period indicated by the
    authentication server. Once the token is expired, a new token is fetched.
    It is thus a good idea to keep a single instance of this class instead of
    re-creating an instance on demand.

    The token caching is internal to this class and opaque to the caller.
    """

    # pylint: disable=too-many-instance-attributes

    def __init__(
        self,
        url: str,
        clientid: str,
        clientsecret: str,
        session: HttpMethodsProtocol = None,
        timer: Callable[[], float] = None,
    ):
        """
        Constructor.

        The ```session``` and ```timer`` parameters are mainly useful for unit testing
        and have useful defaults.

        See :func:`construct_from_service_key` to create an instance from a service key
        instead of giving the individual parameters.

        :param url: URL of OAuth server from DAR credentials
        :param clientid: clientid from DAR credentials
        :param clientsecret: clientsecret from DAR credentials
        :param session: Optional: HTTP session class
        :param timer: Optional: Timer function used for caching
        """
        # pylint: disable=too-many-arguments

        enforce_https_except_localhost(url)

        self._token = None
        self._token_expires_at = 0
        self.url = url
        self.clientid = clientid
        self.clientsecret = clientsecret
        self.session = session or TimeoutRetrySession()
        self.timer = timer or time.monotonic

    @classmethod
    def construct_from_service_key(cls, service_key: dict) -> "OnlineCredentialsSource":

        # pylint: disable=fixme
        # TODO: ensure doctests are executed.
        """
        Creates an instance from a DAR service key.

        .. doctest::

            >>> # service_key is abbreviated from real example
            >>> service_key = {
            ...  "uaa": {
            ...   "clientid": "sb-d3287831-4997-9deb-a09cf1dcf!b4321|dar-v3-std!b4321",
            ...   "clientsecret": "XXXXXX",
            ...   "url": "https://abcd.authentication.sap.hana.ondemand.com",
            ...  },
            ...  "url": "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/"
            ... }
            >>> source = OnlineCredentialsSource.construct_from_service_key(service_key)
            >>> source.url
            'https://abcd.authentication.sap.hana.ondemand.com'

        :param service_key: DAR service key as Python dictionary
        :return: CredentialsSource instance
        """
        uaa = service_key["uaa"]
        return cls(
            url=uaa["url"], clientid=uaa["clientid"], clientsecret=uaa["clientsecret"]
        )

    def token(self) -> str:
        if self._token_expires_at < self.timer():
            self._token = None

        if not self._token:
            payload = self._fetch_token_from_auth_server()
            self._token = payload["access_token"]
            self._token_expires_at = self.timer() + payload["expires_in"]
            # add a 5m grace period: retrieve token earlier.
            self._token_expires_at = self._token_expires_at - 300
        if self._token is None:
            # This check mainly exists to signal to the mypy type checker
            # that the return value cannot be None
            raise ValueError("Token not found in authentication server response!")
        return self._token

    def _fetch_token_from_auth_server(self) -> dict:
        url = self.url + "/oauth/token?grant_type=client_credentials"
        self.log.debug('Retrieving token from URL: "%s"', url)
        response = self.session.get(url, auth=(self.clientid, self.clientsecret))
        response.raise_for_status()
        payload = response.json()
        self.log.debug(
            'Got token for clientid "%s" with HTTP status "%s" and scope "%s"',
            self.clientid,
            response.status_code,
            payload["scope"],
        )
        return payload
