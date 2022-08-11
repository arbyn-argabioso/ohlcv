"""Tests for trading.websockets.logging."""

from unittest import mock
import logging as _logging

import pytest

from ohlcv import logging


@pytest.fixture(name="logger", scope="class")
def fixture_logger():
    return logging.get_logger()


class TestLogging:
    def test__logging__get_logger_correct_return(self):
        assert isinstance(logging.get_logger(), _logging.Logger)

    @pytest.mark.parametrize(
        "input_value, expected_output",
        (
            (logging.CRITICAL, _logging.CRITICAL),
            (logging.WARNING, _logging.WARNING),
            (logging.DEBUG, _logging.DEBUG),
            (logging.ERROR, _logging.ERROR),
            (logging.FATAL, _logging.FATAL),
            (logging.INFO, _logging.INFO),
            (logging.WARN, _logging.WARN),
            (logging.Logger, _logging.Logger),
        ),
    )
    def test__logging__verbosity_levels(self, input_value, expected_output):
        assert input_value == expected_output

    def test__logging__logger_running(self, logger):
        logger.running("Running message")

    def test__logging__logger_success(self, logger):
        logger.success("Success message")

    @mock.patch("ohlcv.logging.os.environ.get")
    def test__logging__get_json_indent(self, os_environ_get):
        os_environ_get.return_value = 1
        assert logging._get_json_indent() == 1

        os_environ_get.return_value = 0
        assert logging._get_json_indent() is None

        os_environ_get.side_effect = "Invalid Number"
        assert logging._get_json_indent() is None
