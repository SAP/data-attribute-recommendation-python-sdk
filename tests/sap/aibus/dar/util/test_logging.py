from logging import Logger

from sap.aibus.dar.client.util.logging import LoggerMixin


class ExampleClass(LoggerMixin):
    pass


class TestLoggerMixin:
    def test(self):
        instance = ExampleClass()

        assert hasattr(instance, "log")

        assert isinstance(instance.log, Logger)

        assert instance.log.name == "tests.sap.aibus.dar.util.test_logging.ExampleClass"
