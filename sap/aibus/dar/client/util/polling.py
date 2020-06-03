"""
This module contains a busy-wait polling implementation.
"""
import time
from typing import Callable

from typing import TypeVar

from sap.aibus.dar.client.util.logging import LoggerMixin

DEFAULT_TIMEOUT_SECONDS = 4 * 60 * 60

DEFAULT_INTERVAL_SECONDS = 30

PolledItem = TypeVar("PolledItem")


class PollingTimeoutException(Exception):
    """
    Exception to indicate that polling did not suceed before timeout.
    """

    pass


class Polling(LoggerMixin):
    """
    Simple busy-wait polling implementation: execute until a condition becomes true.
    """

    def __init__(
        self,
        intervall_seconds: int = DEFAULT_INTERVAL_SECONDS,
        timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    ):
        self._seconds_between_polls = intervall_seconds
        self._timeout_seconds = timeout_seconds

    @staticmethod
    def sleep(how_long: float) -> None:
        """
        Sleeps for a certain amount of time.

        :param how_long: how long to sleep, in seconds
        :return: None
        """
        time.sleep(how_long)

    @staticmethod
    def timer() -> float:
        """
        Returns the current timer value in seconds.

        Note that this value does not necessarily correspond to
        the system clock or the wall clock.

        The Python documentation for the internally used
        :py:func:`time.monotonic` states:

            The reference point of the returned value is undefined,
            so that only the difference between the results of consecutive calls
            is valid.

        :return: current timer value
        """
        return time.monotonic()

    def poll_until_success(
        self,
        polling_function: Callable[[], PolledItem],
        success_function: Callable[[PolledItem], bool],
    ) -> PolledItem:
        """
        Calls *polling_function* until *success_function* returns *True*.

        The output of the *polling_function* will be the input to the
        *success_function*.
        The *polling_function* will be called repeatedly until the *success_function*
        returns *True*.

        Between calls to *polling_function*, this method will sleep.

        :param polling_function: Function which retrieves an item
        :param success_function: Function which checks item for success
        :raises: PollingTimeoutException
        :return: final output of *polling_function*
        """
        start_timestamp = self.timer()
        polling_result = polling_function()
        while not success_function(polling_result):
            remaining = self._timeout_seconds - (self.timer() - start_timestamp)
            if remaining <= 0:
                self.log.info(
                    "Polling did not finish before timeout."
                    " Last observed polling_result: %s",
                    polling_result,
                )
                raise PollingTimeoutException(
                    "Polling did not finish before"
                    " timeout ({}s)".format(self._timeout_seconds)
                )
            time_to_sleep = min(remaining, self._seconds_between_polls)
            self.log.debug(
                "success_function returns false. Sleeping for %s seconds", time_to_sleep
            )

            self.sleep(time_to_sleep)
            polling_result = polling_function()
        self.log.debug("success_function returned true. Polling finished!")
        return polling_result
