"""Module containing a custom JSON logger."""

from __future__ import annotations

from datetime import datetime
from datetime import timezone
import logging as _logging
import os

from pythonjsonlogger import jsonlogger as json_logging


# fmt: off
__all__ = [
    # Constant exports
    "CRITICAL",
    "DEBUG",
    "ERROR",
    "FATAL",
    "INFO",
    "WARN",
    "WARNING",

    # Variable exports
    "Logger",

    # Function exports
    "get_logger",
]
# fmt: on


# Logging levels, standard for logging extensions
DEBUG = _logging.DEBUG
INFO = _logging.INFO
WARNING = _logging.WARNING
WARN = _logging.WARN
ERROR = _logging.ERROR
CRITICAL = _logging.CRITICAL
FATAL = _logging.FATAL

# Standard Logger reference
Logger = _logging.Logger


class _SuccessAndRunningLogger(_logging.Logger):
    def success(self, *args, **kwargs):
        self._success_running("Success", *args, **kwargs)

    def running(self, *args, **kwargs):
        self._success_running("Running", *args, **kwargs)

    def _success_running(self, status: str, *args, **kwargs) -> None:
        extra = kwargs.pop("extra", {})
        if not extra:
            extra = {}
        new_extra = {"status": status}
        new_extra.update(extra)
        self.info(*args, extra=new_extra, **kwargs)


class _JSONFormatter(json_logging.JsonFormatter):
    def add_fields(
        self,
        log_record: dict,
        record: _logging.LogRecord,
        message_dict: dict,
    ):
        log_record["level"] = log_record.get("level", record.levelname).upper()
        log_record["timestamp"] = datetime.fromtimestamp(
            record.created,
            tz=timezone.utc,
        )

        super().add_fields(log_record, record, message_dict)


def get_logger(name: str | None = None, level: int = _logging.INFO, **kwargs):
    """Returns a logger object with additional JSON logging."""

    # Create the logger and set the wanted logging level
    _logging.setLoggerClass(_SuccessAndRunningLogger)
    logger = _logging.getLogger(name or "etl-ohlcv")
    logger.setLevel(level)

    # Create the JSON formatter instance
    logger_formatter = _JSONFormatter(
        json_indent=_get_json_indent(),
        timestamp=False,
    )

    # Check if we already have a handler (for AWS lambda really)
    if len(logger.handlers) != 0:
        logger.handlers[0].setFormatter(logger_formatter)
    else:
        logger_handler = _logging.StreamHandler()
        logger_handler.setFormatter(logger_formatter)
        logger.addHandler(logger_handler)

    return logger


def _get_json_indent() -> int | None:
    """Returns indent from environment variable `TWS_JSON_LOG_INDENT`."""
    tws_json_log_indent = os.environ.get("TWS_JSON_LOG_INDENT")

    try:
        return int(tws_json_log_indent) or None

    except Exception:
        # We can pass here because we want the function to
        # proceed if `TWS_JSON_LOG_INDENT` is not a valid int
        pass

    return None
