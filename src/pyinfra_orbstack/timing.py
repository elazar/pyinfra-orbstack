"""
Simple timing utility for OrbStack operations.

Provides a context manager and decorator for timing operations with consistent
logging output. Uses standard Python logging for integration with existing
logging infrastructure.
"""

import functools
import logging
import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Callable, Optional, TypeVar

# Type variable for generic decorator
F = TypeVar("F", bound=Callable[..., Any])

logger = logging.getLogger(__name__)


@contextmanager
def timed_operation(operation_name: str) -> Iterator[None]:
    """
    Context manager for timing an operation.

    Usage:
        with timed_operation("vm_create"):
            # operation code here
            pass

    Args:
        operation_name: Name of the operation being timed

    Yields:
        None
    """
    start_time = time.time()
    logger.info(f"Starting {operation_name}")

    try:
        yield
    finally:
        elapsed = time.time() - start_time
        logger.info(f"Completed {operation_name} in {elapsed:.2f}s")


def timed(operation_name: Optional[str] = None) -> Callable[[F], F]:
    """
    Decorator for timing function execution.

    Can be used with or without arguments:
        @timed
        @timed()
        @timed("custom_name")

    Args:
        operation_name: Optional custom operation name (defaults to function name)

    Returns:
        Decorated function with timing

    Example:
        @timed("vm_create")
        def create_vm(name: str) -> bool:
            # Implementation
            return True

        @timed  # Uses function name
        def another_operation():
            pass
    """

    def decorator(func: F) -> F:
        op_name = operation_name if operation_name else func.__name__

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            logger.info(f"Starting {op_name}")

            try:
                result = func(*args, **kwargs)
                elapsed = time.time() - start_time
                logger.info(f"Completed {op_name} in {elapsed:.2f}s")
                return result
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(f"Failed {op_name} after {elapsed:.2f}s: {e}")
                raise

        return wrapper  # type: ignore

    # Handle both @timed and @timed() usage
    if operation_name is None or callable(operation_name):
        # Called as @timed without parentheses
        if callable(operation_name):
            func = operation_name
            operation_name = None
            return decorator(func)

    return decorator


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for timing output.

    Args:
        level: Logging level (default: logging.INFO)

    Example:
        # Enable verbose timing logs
        from pyinfra_orbstack.timing import configure_logging
        import logging

        configure_logging(logging.DEBUG)
    """
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=level,
    )
