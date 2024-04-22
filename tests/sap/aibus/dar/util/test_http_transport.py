from typing import Any, Set
from unittest.mock import Mock, create_autospec

import pytest
from requests import Session

from sap.aibus.dar.client.exceptions import HTTPSRequired
from sap.aibus.dar.client.util import http_transport
from sap.aibus.dar.client.util.http_transport import (
    RetrySession,
    TimeoutSession,
    TimeoutRetrySession,
    PostRetrySession,
    TimeoutPostRetrySession,
)


class _BaseHTTPSEnforcedTest:
    def test_https_enforced(self):
        """
        Non-HTTPS URLs are rejected
        :return:
        """
        url = "http://aiservices-dar.cfapps.xxx.hana.ondemand.com/"
        session = self.create_test_object()
        verbs = ["get", "put", "delete", "post", "patch", "request"]
        for verb in verbs:
            with pytest.raises(HTTPSRequired):
                getattr(session, verb)(url)

    def create_test_object(self):
        raise NotImplementedError()


class _BaseRetrySessionTest(_BaseHTTPSEnforcedTest):
    num_retries = 3
    class_under_test = None  # type: Any
    expected_allowed_methods = set()  # type: Set[str]

    def test_default_session(self):
        session = self.class_under_test(self.num_retries, session=None)
        expected_schemes = ["http://", "https://"]
        for scheme, adapter in session.adapters.items():
            assert scheme in expected_schemes
            expected_schemes.remove(scheme)

            self._assert_retry_set_up_correctly(adapter)
        assert len(expected_schemes) == 0

    def test_can_override_session(self):
        mock_session = create_autospec(Session, instance=True)

        session = self.class_under_test(self.num_retries, session=mock_session)

        assert mock_session.mount.call_count == 2

        assert session.session == mock_session

        for cal in mock_session.mount.call_args_list:
            adapter = cal[0][1]
            self._assert_retry_set_up_correctly(adapter)

    def _assert_retry_set_up_correctly(self, adapter):
        retry = adapter.max_retries
        assert retry.total == self.num_retries
        assert retry.read == self.num_retries
        assert retry.connect == self.num_retries
        assert retry.allowed_methods == self.expected_allowed_methods

    def create_test_object(self):
        return self.class_under_test(self.num_retries, session=None)


class TestRetrySession(_BaseRetrySessionTest):
    class_under_test = RetrySession
    expected_allowed_methods = set({"GET", "PUT", "DELETE"})


class TestPostRetrySession(_BaseRetrySessionTest):
    class_under_test = PostRetrySession
    expected_allowed_methods = set({"GET", "PUT", "DELETE", "POST"})


class TestTimeoutSession(_BaseHTTPSEnforcedTest):
    url = "https://localhost/"

    def setup_method(self):
        self.mock_inner_session = Mock()
        self.session = TimeoutSession(self.mock_inner_session)
        self.verbs = ["get", "put", "delete", "post", "patch", "request"]

    def test_constructor(self):
        session = TimeoutSession()
        assert session.session is not None
        assert hasattr(session.session, "get") is True
        assert session.read_timeout == http_transport.READ_TIMEOUT
        assert session.connect_timeout == http_transport.CONNECT_TIMEOUT

    def test_http_methods(self):
        for verb in self.verbs:
            # act
            self._check_http_method(verb)

    def _check_http_method(self, verb):
        getattr(self.mock_inner_session, verb).return_value = "response"
        response = getattr(self.session, verb)(self.url)
        assert response == "response"

        assert getattr(self.mock_inner_session, verb).call_count == 1
        call_args = getattr(self.mock_inner_session, verb).call_args[0]
        call_kwargs = getattr(self.mock_inner_session, verb).call_args[1]
        assert call_args == (self.url,)
        assert call_kwargs == {"timeout": (240, 240)}

    def test_http_method_with_header(self):
        for verb in self.verbs:
            # act
            self._check_http_method_with_header(verb)

    def _check_http_method_with_header(self, verb):
        getattr(self.session, verb)(self.url, header={"key": "value"})
        assert getattr(self.mock_inner_session, verb).call_count == 1
        call_args = getattr(self.mock_inner_session, verb).call_args[0]
        call_kwargs = getattr(self.mock_inner_session, verb).call_args[1]
        assert call_args == (self.url,)
        assert call_kwargs == {"timeout": (240, 240), "header": {"key": "value"}}

    def create_test_object(self):
        return self.session


class _BaseTestRetryTimeoutSession(_BaseHTTPSEnforcedTest):
    class_under_test = None  # type: Any
    expected_retry_session_class = None  # type: Any

    def test_constructor(self):
        session = self.class_under_test()
        assert session is not None

    def test_constructor_args(self):
        session = self.class_under_test(3, read_timeout=10, connect_timeout=99)
        timeout_session = session.session
        assert timeout_session.read_timeout == 10
        assert timeout_session.connect_timeout == 99

    def test_constructor_num_retries(self):
        session = self.class_under_test(99)

        # check default parameters
        for adapter in session.adapters.values():
            retry = adapter.max_retries
            assert retry.total == 99
            assert retry.read == 99
            assert retry.connect == 99

    def test_nested_session(self):
        sess = self.class_under_test(3)
        assert isinstance(sess.session, TimeoutSession)
        assert isinstance(sess.session.session, self.expected_retry_session_class)

    def test_http_methods(self):
        url = "https://localhost/"
        session = self.class_under_test(3)
        mock_inner_session = Mock()
        session.session = mock_inner_session
        verbs = ["get", "put", "delete", "post", "patch", "request"]
        for verb in verbs:
            getattr(session, verb)(url)
            assert getattr(mock_inner_session, verb).call_count == 1

    def create_test_object(self):
        return self.class_under_test(3)


class TestRetryTimeoutSession(_BaseTestRetryTimeoutSession):
    """
    Tests TimeoutRetrySession.

    The internally used Retry implementation should be RetrySession.
    """

    class_under_test = TimeoutRetrySession
    expected_retry_session_class = RetrySession


class TestPostRetryTimeoutSession(_BaseTestRetryTimeoutSession):
    """
    Tests TimeoutPostRetrySession

    This should behave identically to TimeoutRetrySession, but use
    PostRetrySession as Retry implementation.
    """

    class_under_test = TimeoutPostRetrySession
    expected_retry_session_class = PostRetrySession
