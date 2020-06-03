import math
import time
from unittest.mock import Mock, call, create_autospec

import pytest

from sap.aibus.dar.client.util.polling import Polling, PollingTimeoutException


class TestPolling:
    def test_basic_functionality(self):
        values = [{"status": "PENDING"}, {"status": "RUNNING"}, {"status": "SUCCEEDED"}]

        polling_function = Mock()
        polling_function.side_effect = values

        def check_function_side_effect(item: dict):
            if "status" in item and item["status"] in ["PENDING", "RUNNING"]:
                return False
            return True

        check_function = Mock()
        check_function.side_effect = check_function_side_effect

        p = Polling()
        p.sleep = Mock()

        observed_result = p.poll_until_success(polling_function, check_function)

        expected_result = {"status": "SUCCEEDED"}

        assert observed_result == expected_result

        assert polling_function.call_count == 3

        expected_calls_to_check_function = [
            call({"status": "PENDING"}),
            call({"status": "RUNNING"}),
            call({"status": "SUCCEEDED"}),
        ]
        assert check_function.call_args_list == expected_calls_to_check_function

        expected_calls_to_sleep = [call(30), call(30)]

        assert p.sleep.call_args_list == expected_calls_to_sleep

    def test_timeout(self):
        clock = MockClock()

        timeout_seconds = 300
        intervall_seconds = 30
        time_per_poll = 2

        def polling_function():
            # every call takes 2 seconds
            clock.advance_clock(time_per_poll)
            return None

        def check_function(_):
            # We are never done
            return False

        mock_polling_function = Mock(side_effect=polling_function)

        p = Polling(timeout_seconds=timeout_seconds)
        # sleeping advances the clock by the time slept
        p.sleep = Mock(side_effect=clock.advance_clock)
        p.timer = clock.read_clock

        with pytest.raises(PollingTimeoutException) as exc_info:
            p.poll_until_success(
                polling_function=mock_polling_function, success_function=check_function
            )

        expected_message = "Polling did not finish before timeout ({}s)".format(
            timeout_seconds
        )

        assert str(exc_info.value) == expected_message

        # We always poll one last time after the timeout has elapsed.
        assert clock.read_clock() == timeout_seconds + time_per_poll

        #
        expected_sleep_count = timeout_seconds / (intervall_seconds + time_per_poll)
        # Round up because we will always use the time granted until timeout
        expected_sleep_count = math.ceil(expected_sleep_count)
        assert p.sleep.call_count == expected_sleep_count

    def test_polling_interval_is_configurable(self):
        values = [False, False, True]

        def polling_function():
            return values.pop(0)

        def check_function(value: bool) -> bool:
            return value

        p = Polling(intervall_seconds=2)

        p.sleep = create_autospec(time.sleep)

        p.poll_until_success(polling_function, check_function)

        expected_sleep_calls = [call(2), call(2)]

        assert p.sleep.call_args_list == expected_sleep_calls


class MockClock:
    """
    A mock clock. Can be advanced at will.
    """

    def __init__(self):
        self.seconds = 0.0

    def advance_clock(self, seconds: float):
        self.seconds += seconds

    def read_clock(self):
        return self.seconds
