# pylint: disable=fixme
# TODO: remove

"""
This module contains implementations of best practices
for the interaction with other services over HTTP.
"""
from typing import Tuple

from requests.adapters import HTTPAdapter
from requests import Session, Response
from typing_extensions import Protocol

from urllib3 import Retry

from sap.aibus.dar.client.exceptions import HTTPSRequired

READ_TIMEOUT = 240

CONNECT_TIMEOUT = 240

NUM_REQUEST_RETRIES = 7  # total number of request retries


class HttpMethodsProtocol(Protocol):
    """
    A protocol describing a basic HTTP client.

    This is a Protocol to support structural subtyping via mypy.
    In the Java world, this would be similar to an Interface.
    """

    # Disable pylint checks: not relevant for Protocol/ABC.
    # pylint: disable=unused-argument,no-self-use,pointless-statement,missing-docstring

    def request(self, *wargs, **kwargs) -> Response:
        ...

    def get(self, *args, **kwargs) -> Response:
        ...

    def post(self, *args, **kwargs) -> Response:
        ...

    def put(self, *args, **kwargs) -> Response:
        ...

    def delete(self, *args, **kwargs) -> Response:
        ...

    def patch(self, *args, **kwargs) -> Response:
        ...


class HttpMethodsMixin(HttpMethodsProtocol):
    """
    A mixin dispatching common HTTP methods to a `session` property.
    """

    def default_kwargs(self) -> dict:  # pylint: disable=no-self-use
        """
        A default set of keyword arguments to be passed to each invocation of
        a HTTP method on the `session`.

        This default implementation returns an empty dictionary.

        :return: an empty dictionary
        """
        return {}

    def __handle(self, verb, url, *args, **kwargs):
        enforce_https_except_localhost(url)
        kwargs.update(self.default_kwargs())
        return getattr(self.session, verb)(url, *args, **kwargs)

    def post(self, *args, **kwargs):
        r"""
        Invokes the *post* method with given arguments on the *session*.

        :param \*args: Any args to be passed to *session.post*
        :param \**kwargs: Any keyword args to be passed to *session.post*

        :return: the return value of *session.post*
        """
        return self.__handle("post", *args, **kwargs)

    def get(self, *args, **kwargs):
        r"""
        Invokes the *get* method with given arguments on the *session*.

        Args:
        :param \*args: Any args to be passed to *session.get*
        :param \**kwargs: Any keyword args to be passed to *session.get*

        :return: the return value of *session.get*
        """
        return self.__handle("get", *args, **kwargs)

    def request(self, *args, **kwargs):
        r"""
        Invokes the *request* method with given arguments on the *session*.

        :param: \*args: Any args to be passed to *session.request*
        :param: \**kwargs: Any keyword args to be passed to *session.request*

        :return: the return value of *session.request*
        """
        return self.__handle("request", *args, **kwargs)

    def put(self, *args, **kwargs):
        r"""
        Invokes the *put* method with given arguments on the *session*.

        :param \*args: Any args to be passed to *session.put*
        :param \**kwargs: Any keyword args to be passed to *session.put*

        :return:    the return value of *session.put*
        """
        return self.__handle("put", *args, **kwargs)

    def delete(self, *args, **kwargs):
        r"""
        Invokes the *delete* method with given arguments on the *session*.

        Args:
        :param \*args: Any args to be passed to *session.delete*
        :param \**kwargs: Any keyword args to be passed to *session.delete*

        :return: the return value of *session.delete*
        """
        return self.__handle("delete", *args, **kwargs)

    def patch(self, *args, **kwargs):
        r"""
        Invokes the *patch* method with given arguments on the *session*.

        :param \*args: Any args to be passed to *session.patch*
        :param \**kwargs: Any keyword args to be passed to *session.patch*

        :return: the return value of *session.patch*
        """
        return self.__handle("patch", *args, **kwargs)

    @property
    def adapters(self):
        """
        Returns adapters of internally used session.

        This is mainly useful for unit tests.
        """
        return self.session.adapters


class RetrySession(HttpMethodsMixin):  # pylint: disable=too-few-public-methods
    """
    HTTP connection with retry built-in.

    Retry is allowed for GET, PUT and DELETE HTTP method verbs.
    """

    def __init__(
        self,
        num_retries: int,
        session: Session = None,
        backoff_factor: float = 0.05,
        status_forcelist: Tuple = (413, 429, 500, 502, 503, 504),
    ):
        """
        Constructor.

        :param num_retries: number of retries (total number of retries, as well as
            number of retries on connection-related, read errors, on bad statuses)
        :param session: requests session
        :param backoff_factor: factor that controls delay between single retry attempts
        :param status_forcelist: a set of integer HTTP response codes that will lead
            to retry.
        """
        super().__init__()
        session = session or Session()
        retry = Retry(
            total=num_retries,
            read=num_retries,
            connect=num_retries,
            status=num_retries,
            backoff_factor=backoff_factor,
            allowed_methods=self._get_method_whitelist(),
            status_forcelist=status_forcelist,
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        self.session = session

    @staticmethod
    def _get_method_whitelist():
        return frozenset(["GET", "PUT", "DELETE"])


class PostRetrySession(RetrySession):
    """
    A RetrySession with retry enabled for *POST* requests.

    This is identical to :class:`RetrySession`, but enables retries
    for POST requests as well.
    POST is not retried by default in :class:`RetrySession`. *POST*
    is not an `Idempotent Method`_ and is thus not guaranteed to be safe
    for retries.

    This class should only be used with endpoints where retrying will not lead
    to undesired side-effects or where the side-effect is tolerable.

    Note that connection-related errors which occur before the initial connection is
    established are always retried, no matter if the **POST** HTTP method is
    enabled for retries or not.
    For details, refer to the underlying implementation: see the documentation on
    the **connect** parameter in :class:`urllib3.util.retry.Retry`.

    See :ref:`retry` for trade-offs involved here.

    .. _Idempotent Method: https://tools.ietf.org/html/rfc7231#section-4.2.2
    """

    @staticmethod
    def _get_method_whitelist():
        return frozenset(["GET", "PUT", "DELETE", "POST"])


class TimeoutSession(HttpMethodsMixin):
    """
    Session implementing timeouts to prevent HTTP connections from blocking
    indefinitely.

    By default, the `requests` module does not set a timeout, resulting in
    connections which can take forever. This class implements a sane timeout policy.

    Note that this class does not protect against slow connections: if the server
    sends one byte per second, the timeout will not expire (unless set to < 1s). The
    read timeout only applies to the intervals between data transfers.
    """

    def __init__(
        self,
        session: HttpMethodsProtocol = None,
        connect_timeout: float = CONNECT_TIMEOUT,
        read_timeout: float = READ_TIMEOUT,
    ):
        """
        Constructor.

        :param session: requests Session or compatible
        :param connect_timeout: timeout for the connection
        :param read_timeout: maximum time between bytes after connect
        """
        super().__init__()
        self.session = session or Session()

        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout

    def default_kwargs(self) -> dict:
        """
        Implements the timeout policy.

        :return: keyword args implementing the timeout policy.
        """
        return {"timeout": (self.connect_timeout, self.read_timeout)}


class TimeoutRetrySession(HttpMethodsMixin):
    """
    A session combining timeout and retry policies.

    If a request times out, it is retried.

    This can be tested manually as follows:

    ...doctest::

        >>> sess = TimeoutRetrySession(read_timeout=1)
        >>> # Remove +SKIP below to execute next line
        >>> sess.get('https://httpstat.us/200?sleep=2000') # doctest: +ELLIPSIS, +SKIP
        Traceback (most recent call last):
        ...
        requests.exceptions.ConnectionError: ... Max retries exceeded with url: ...
    """

    def __init__(
        self,
        num_retries: int = NUM_REQUEST_RETRIES,
        connect_timeout: float = CONNECT_TIMEOUT,
        read_timeout: float = READ_TIMEOUT,
    ):
        """
        Constructor.

        See `TimeoutSession` for a discussion of the values.

        Args:
            num_retries: Number of retries
            connect_timeout: connect timeout
            read_timeout: read timeout
        """
        super().__init__()
        retry_session = self._make_retry_session(num_retries)
        timeout_session = TimeoutSession(
            session=retry_session,
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
        )
        self.session = timeout_session

    @staticmethod
    def _make_retry_session(num_retries):
        return RetrySession(num_retries)


class TimeoutPostRetrySession(TimeoutRetrySession):
    """
    A TimeoutRetrySession which retries on *POST*.

    This is identical to :class:`TimeoutRetrySession`, but
    uses :class:`PostRetrySession` internally to implement retries for *POST*.

    Note that retries for POST are no always see. See the remarks on
    :class:`PostRetrySession`.
    """

    @staticmethod
    def _make_retry_session(num_retries):
        return PostRetrySession(num_retries)


def enforce_https_except_localhost(url: str):
    """
    Raises HTTPSRequired exception if required.

    :param url: URL to be checked
    :return: None
    :raises HTTPSRequired: if given url does not start with https
    """
    if not url.startswith("https") and not url.startswith("http://localhost"):
        raise HTTPSRequired
