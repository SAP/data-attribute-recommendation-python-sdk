from logging import Logger
import sys
from unittest.mock import patch, call

from sap.aibus.dar.client.util.logging import LoggerMixin


class ExampleClass(LoggerMixin):
    pass


class TestLoggerMixin:
    def test(self):
        instance = ExampleClass()

        assert hasattr(instance, "log")

        assert isinstance(instance.log, Logger)

        assert instance.log.name == "tests.sap.aibus.dar.util.test_logging.ExampleClass"

    @patch("sap.aibus.dar.client.util.logging.logging", autospec=True)
    def test_setup_basic_logging(self, logging_mock):
        LoggerMixin.setup_basic_logging()

        assert logging_mock.basicConfig.call_args_list == [
            call(level=logging_mock.INFO, stream=sys.stdout)
        ]

    @patch("sap.aibus.dar.client.util.logging.logging", autospec=True)
    def test_setup_basic_logging_debug(self, logging_mock):
        LoggerMixin.setup_basic_logging(debug=True)

        assert logging_mock.basicConfig.call_args_list == [
            call(level=logging_mock.DEBUG, stream=sys.stdout)
        ]
