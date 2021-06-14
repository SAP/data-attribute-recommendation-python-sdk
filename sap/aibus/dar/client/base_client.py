"""
Shared infrastructure for microservice clients.
"""
from typing import TypeVar, Type

from cfenv import AppEnv

from sap.aibus.dar.client.util.credentials import (
    CredentialsSource,
    OnlineCredentialsSource,
    StaticCredentialsSource,
)
from sap.aibus.dar.client.dar_session import DARSession
from sap.aibus.dar.client.util.logging import LoggerMixin

DARClient = TypeVar("DARClient", bound="BaseClient")


class BaseClient(LoggerMixin):
    """
    Shared base class for all clients.

    Contains shared class construction methods.
    """

    def __init__(self, url: str, credentials_source: CredentialsSource):
        raise NotImplementedError

    @classmethod
    def construct_from_credentials(
        cls: Type[DARClient],
        dar_url: str,
        clientid: str,
        clientsecret: str,
        uaa_url: str,
    ) -> DARClient:
        """
        Constructs a DARClient from credentials.

        The credentials can be obtained from a service key. If a service key is
        available, see :meth:`construct_from_service_key`.

        :param dar_url: Service URL
        :param clientid: Client ID
        :param clientsecret: Client Secret
        :param uaa_url: Authentication URL
        :return: the client instance
        """
        source = OnlineCredentialsSource(uaa_url, clientid, clientsecret)
        return cls(dar_url, source)

    @classmethod
    def construct_from_service_key(
        cls: Type[DARClient], service_key: dict
    ) -> DARClient:
        """
        Constructs a DARClient from a service key.

        The service key should be provided as a Python *dict* after decoding it from
        JSON.

        :param service_key: DAR service key
        :return: the client instance
        """
        return cls.construct_from_credentials(
            service_key["url"],
            service_key["uaa"]["clientid"],
            service_key["uaa"]["clientsecret"],
            service_key["uaa"]["url"],
        )

    @classmethod
    def construct_from_jwt(cls: Type[DARClient], dar_url: str, token: str) -> DARClient:
        """
        Constructs a DARClient from service URL and a static token.

        This is useful if a pre-existing token should be used instead of retrieving
        new tokens at runtime.

        .. note::
            Tokens expire after a certain amount of time, usually after several hours.
            It is preferable to use :meth:`construct_from_service_key` or
            :meth:`construct_from_credentials`.

        :param dar_url: Service URL
        :param token: Service token
        :return: the client instance
        """
        source = StaticCredentialsSource(token)
        return cls(dar_url, source)

    @classmethod
    def construct_from_cf_env(cls: Type[DARClient]) -> DARClient:
        """
        Constructs a DARClient from service binding in a CloudFoundry app.

        This is useful when the SDK is used in a CloudFoundry application on the
        SAP Business Technology Platform where the application is bound to an instance
        of the Data Attribute Recommendation service.

        This constructor assumes that only one instance of the service is bound
        to the app.
        :return: the client instance
        """
        env = AppEnv()
        dar = env.get_service(label="data-attribute-recommendation")
        return cls.construct_from_service_key(dar.credentials)


class BaseClientWithSession(BaseClient):
    """
    Base class for individual microservice clients.
    """

    def __init__(self, url: str, credentials_source: CredentialsSource):
        self.credentials_source = credentials_source
        self.session = DARSession(url, credentials_source)
