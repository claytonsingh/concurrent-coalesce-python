import pytest
import sys

# For Python < 3.5, create empty test functions that are skipped
@pytest.mark.skip(reason="Async tests require Python 3.5+")
def test_async_basic_functionality():
    pass

@pytest.mark.skip(reason="Async tests require Python 3.5+")
def test_async_concurrency_same_args():
    pass

@pytest.mark.skip(reason="Async tests require Python 3.5+")
def test_async_concurrency_different_args():
    pass

@pytest.mark.skip(reason="Async tests require Python 3.5+")
def test_async_exception_handling():
    pass

@pytest.mark.skip(reason="Async tests require Python 3.5+")
def test_async_concurrent_exceptions():
    pass

@pytest.mark.skip(reason="Async tests require Python 3.5+")
def test_async_custom_key_function():
    pass

@pytest.mark.skip(reason="Async tests require Python 3.5+")
def test_async_future_reset():
    pass

@pytest.mark.skip(reason="Async tests require Python 3.5 to 3.10")
def test_coroutine_decorator_style():
    pass

# Only import and run actual async tests on Python 3.5+
if sys.version_info >= (3, 5): 
    from _async_tests import *  # noqa
