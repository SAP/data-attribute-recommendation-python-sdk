"""
Logging functionality.
"""
import logging
import sys


class LoggerMixin:
    """
    A log mixin. Provides a :meth:`log` property.
    """

    @property
    def log(self) -> logging.Logger:
        """
        Returns a log instance for this class.

        :return: log for this class
        """
        return logging.getLogger(
            self.__class__.__module__ + "." + self.__class__.__name__
        )

    @staticmethod
    def setup_basic_logging(debug=False) -> None:
        """
        Initializes basic logging to stdout.

        This is ideal for use in scripts to observe what actions the client library
        is performing.

        It is not recommended to call this if the library is used in a bigger
        project, where usually custom logging setup is desired.
        """
        level = logging.INFO
        if debug:
            level = logging.DEBUG
        logging.basicConfig(level=level, stream=sys.stdout)
