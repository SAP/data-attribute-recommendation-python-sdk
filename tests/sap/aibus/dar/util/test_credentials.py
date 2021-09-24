import time
from unittest.mock import create_autospec, call, Mock

import pytest

from sap.aibus.dar.client.exceptions import HTTPSRequired
from sap.aibus.dar.client.util.credentials import (
    OnlineCredentialsSource,
    CredentialsSource,
    StaticCredentialsSource,
)
from sap.aibus.dar.client.util.http_transport import TimeoutRetrySession


class TestCredentialsSource:
    def test_get_token_has_no_implementation(self):
        source = CredentialsSource()
        with pytest.raises(NotImplementedError):
            source.token()


class TestOfflineCredentialsSource:
    def test_constructor_has_no_defaults(self):
        with pytest.raises(TypeError):
            StaticCredentialsSource()

    def test_constructor_positional_args(self):
        source = StaticCredentialsSource("abcd")
        assert source.token() == "abcd"

    def test_constructor_keyword_args(self):
        source = StaticCredentialsSource(token="abcd")
        assert source.token() == "abcd"


class TestOnlineCredentialsSource:
    """
    Tests various ways to construct the source.
    """

    def test_constructor_has_no_defaults(self):
        with pytest.raises(TypeError):
            OnlineCredentialsSource()

    def test_constructor_positional_args(self):
        source = OnlineCredentialsSource(
            "https://URL", "a-client-id", "a-client-secret"
        )
        self._assert_properties(source)

    def test_constructor_keyword_args(self):
        source = OnlineCredentialsSource(
            url="https://URL", clientid="a-client-id", clientsecret="a-client-secret"
        )
        self._assert_properties(source)

    def test_constructor_positional_args_can_override_session(self):
        mock_session = create_autospec(TimeoutRetrySession, instance=True)
        source = OnlineCredentialsSource(
            "https://URL", "a-client-id", "a-client-secret", mock_session
        )
        assert source.session == mock_session

    def test_constructor_keyword_args_can_override_session(self):
        mock_session = create_autospec(TimeoutRetrySession, instance=True)
        source = OnlineCredentialsSource(
            url="https://URL",
            clientid="a-client-id",
            clientsecret="a-client-secret",
            session=mock_session,
        )
        assert source.session == mock_session

    def test_factory_method_from_service_key(self):
        # abbreviated service key. Irrelevant keys are
        # removed.
        service_key = {
            "uaa": {
                "clientid": "a-client-id",
                "clientsecret": "a-client-secret",
                "url": "https://URL",
            },
            "url": "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/",
        }

        source = OnlineCredentialsSource.construct_from_service_key(service_key)

        self._assert_properties(source)

    def _assert_properties(self, source):
        assert source.url == "https://URL"
        assert source.clientid == "a-client-id"
        assert source.clientsecret == "a-client-secret"
        assert isinstance(source.session, TimeoutRetrySession)


@pytest.fixture()
def online_credentials_source_with_mock_session():
    mock_timer = create_autospec(time.monotonic)
    mock_timer.return_value = 100
    mock_session = create_autospec(TimeoutRetrySession, instance=True)
    mock_response = Mock()
    mock_session.get.return_value = mock_response

    mock_response.json.side_effect = [
        {
            "access_token": "the-token",
            "token_type": "bearer",
            "expires_in": 43199,
            "scope": "scope1 scope2 scope3",
        },
        {
            "access_token": "the-token-2",
            "token_type": "bearer",
            "expires_in": 43199,
            "scope": "scope1 scope2 scope3",
        },
    ]

    source = OnlineCredentialsSource(
        url="https://test.xyz",
        clientid="a-client-id",
        clientsecret="a-client-secret",
        session=mock_session,
        timer=mock_timer,
    )
    return source


class TestOnlineCredentialsSourceTokenRetrieval:
    def test_token_retrieval(self, online_credentials_source_with_mock_session):
        observed_token = online_credentials_source_with_mock_session.token()

        mock_session = online_credentials_source_with_mock_session.session
        mock_response = mock_session.get.return_value

        expected_call_to_get = call(
            "https://test.xyz/oauth/token?grant_type=client_credentials",
            auth=("a-client-id", "a-client-secret"),
        )
        assert mock_session.get.call_args_list == [expected_call_to_get]
        assert mock_response.raise_for_status.call_count == 1
        assert observed_token == "the-token"

    def test_token_retrieval_raises_if_access_token_is_none(
        self, online_credentials_source_with_mock_session
    ):
        mock_response = online_credentials_source_with_mock_session.session.get()
        mock_response.json.side_effect = [
            {
                "access_token": None,
                "token_type": "bearer",
                "expires_in": 43199,
                "scope": "scope1 scope2 scope3",
            }
        ]

        with pytest.raises(ValueError):
            online_credentials_source_with_mock_session.token()

    def test_token_caching(self, online_credentials_source_with_mock_session):
        mock_session = online_credentials_source_with_mock_session.session

        mock_timer = online_credentials_source_with_mock_session.timer

        assert mock_session.get.call_count == 0

        # Pretend that it is eleven hours later, call token() again.
        # We expect to see the cached token retrieved.
        mock_timer.return_value = mock_timer.return_value + (11 * 60 * 60)

        first_token = online_credentials_source_with_mock_session.token()

        assert mock_session.get.call_count == 1

        # When we retrieve then token the second time, we should get the same token
        # as before and no more GET requests should have been made
        second_token = online_credentials_source_with_mock_session.token()

        assert first_token == second_token

        assert mock_session.get.call_count == 1

    def test_token_caching_expires(self, online_credentials_source_with_mock_session):
        mock_session = online_credentials_source_with_mock_session.session
        mock_timer = online_credentials_source_with_mock_session.timer

        assert mock_session.get.call_count == 0

        first_token = online_credentials_source_with_mock_session.token()

        assert first_token == "the-token"

        assert mock_session.get.call_count == 1

        # Now, one day later, call token() again.
        # We expect to see a fresh token retrieved.
        mock_timer.return_value = mock_timer.return_value + (24 * 60 * 60)

        second_token = online_credentials_source_with_mock_session.token()

        assert second_token == "the-token-2"
        assert mock_session.get.call_count == 2


class TestHTTPSEnforced:
    def test_constructor_enforces_https(self):
        with pytest.raises(HTTPSRequired):
            OnlineCredentialsSource(
                url="http://insecure",
                clientid="a-client-id",
                clientsecret="a-client-secret",
            )

    def test_factory_method_from_service_key_https_is_enforced(self):
        service_key = {
            "uaa": {
                "clientid": "a-client-id",
                "clientsecret": "a-client-secret",
                "url": "http://insecure",
            },
            "url": "https://aiservices-dar.cfapps.xxx.hana.ondemand.com/",
        }

        with pytest.raises(HTTPSRequired):
            OnlineCredentialsSource.construct_from_service_key(service_key)

    def test_constructor_allows_http_for_localhost(self):
        try:
            OnlineCredentialsSource(
                url="http://localhost",
                clientid="a-client-id",
                clientsecret="a-client-secret",
            )
        except HTTPSRequired:
            assert False, "Plain-text connection to localhost should be allowed."
