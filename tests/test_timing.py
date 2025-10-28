"""
Tests for timing utility.
"""

import logging
import time

import pytest

from pyinfra_orbstack.timing import timed, timed_operation


def test_timed_operation_context_manager(caplog):
    """Test timed_operation context manager."""
    with caplog.at_level(logging.INFO):
        with timed_operation("test_operation"):
            time.sleep(0.01)  # Small delay

    # Check logging output
    assert "Starting test_operation" in caplog.text
    assert "Completed test_operation in" in caplog.text


def test_timed_operation_with_exception(caplog):
    """Test timed_operation handles exceptions properly."""
    with caplog.at_level(logging.INFO):
        with pytest.raises(ValueError):
            with timed_operation("failing_operation"):
                raise ValueError("Test error")

    # Should still log completion time even on failure
    assert "Starting failing_operation" in caplog.text
    assert "Completed failing_operation in" in caplog.text


def test_timed_decorator_with_name(caplog):
    """Test timed decorator with custom name."""

    @timed("custom_operation")
    def test_func(x: int) -> int:
        time.sleep(0.01)
        return x * 2

    with caplog.at_level(logging.INFO):
        result = test_func(5)

    assert result == 10
    assert "Starting custom_operation" in caplog.text
    assert "Completed custom_operation in" in caplog.text


def test_timed_decorator_without_name(caplog):
    """Test timed decorator uses function name by default."""

    @timed()
    def my_function() -> str:
        return "result"

    with caplog.at_level(logging.INFO):
        result = my_function()

    assert result == "result"
    assert "Starting my_function" in caplog.text
    assert "Completed my_function in" in caplog.text


def test_timed_decorator_no_parens(caplog):
    """Test timed decorator without parentheses."""

    @timed
    def another_function() -> int:
        return 42

    with caplog.at_level(logging.INFO):
        result = another_function()

    assert result == 42
    assert "Starting another_function" in caplog.text
    assert "Completed another_function in" in caplog.text


def test_timed_decorator_with_exception(caplog):
    """Test timed decorator logs errors properly."""

    @timed("failing_func")
    def failing_function() -> None:
        raise RuntimeError("Something went wrong")

    with caplog.at_level(logging.ERROR):
        with pytest.raises(RuntimeError):
            failing_function()

    assert "Failed failing_func after" in caplog.text
    assert "Something went wrong" in caplog.text


def test_timing_accuracy(caplog):
    """Test that timing is reasonably accurate."""

    @timed("timing_test")
    def slow_function() -> None:
        time.sleep(0.1)  # 100ms

    with caplog.at_level(logging.INFO):
        slow_function()

    # Extract timing from log message
    log_message = [r for r in caplog.records if "Completed" in r.message][0].message

    # Should show approximately 0.1s (allow tolerance)
    assert "0.1" in log_message or "0.09" in log_message or "0.11" in log_message


def test_timed_preserves_function_metadata():
    """Test that decorator preserves function metadata."""

    @timed
    def documented_function() -> int:
        """This function has documentation."""
        return 42

    assert documented_function.__name__ == "documented_function"
    assert documented_function.__doc__ == "This function has documentation."


def test_timed_with_args_and_kwargs(caplog):
    """Test timed decorator works with function arguments."""

    @timed("add_numbers")
    def add(a: int, b: int, multiply: int = 1) -> int:
        return (a + b) * multiply

    with caplog.at_level(logging.INFO):
        result = add(3, 4, multiply=2)

    assert result == 14
    assert "Starting add_numbers" in caplog.text
    assert "Completed add_numbers in" in caplog.text
