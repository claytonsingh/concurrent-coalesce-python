import pytest
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from concurrent_coalesce import coalesce

def test_basic_functionality():
    """Test that the decorated function returns the correct result."""
    class AddFunction(object):
        def __init__(self):
            self.call_count = 0
            
        @coalesce()
        def __call__(self, a, b):
            self.call_count += 1
            return a + b
            
    add_func = AddFunction()
    result = add_func(2, 3)
    assert result == 5
    assert add_func.call_count == 1
    
    # Call again with same args - should increment counter
    result = add_func(2, 3)
    assert result == 5
    assert add_func.call_count == 2
    
def test_concurrency_same_args():
    """Test that concurrent calls with same arguments only execute once."""
    class SlowFunction(object):
        def __init__(self):
            self.call_count = 0
            
        @coalesce()
        def __call__(self, x):
            self.call_count += 1
            time.sleep(0.1)  # Small delay to ensure concurrent execution
            return x * 2
            
    slow_func = SlowFunction()
        
    def thread_func():
        return slow_func(5)
        
    # Start threads
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(thread_func) for _ in range(5)]
        results = [f.result() for f in futures]
        
    # All results should be the same
    assert results == [10, 10, 10, 10, 10]
    # Function should only have been called once
    assert slow_func.call_count == 1
    
def test_concurrency_different_args():
    """Test that concurrent calls with different arguments execute separately."""
    class ParameterizedFunction(object):
        def __init__(self):
            self.call_counts = {}
            self.lock = threading.Lock()
            
        @coalesce()
        def __call__(self, key):
            with self.lock:
                self.call_counts[key] = self.call_counts.get(key, 0) + 1
            time.sleep(0.1)  # Small delay to ensure overlap
            return "result-" + str(key)
            
    parameterized_func = ParameterizedFunction()
        
    def thread_func(value):
        return parameterized_func(value)
        
    # Run 10 threads with 5 different values (2 threads per value)
    args = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(thread_func, arg) for arg in args]
        results = [f.result() for f in futures]
        
    # Check that each unique argument was processed once
    assert parameterized_func.call_counts == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
    
    # Verify results
    expected_results = ["result-" + str(arg) for arg in args]
    assert results == expected_results
    
def test_exception_handling():
    """Test that exceptions are properly propagated."""
    
    @coalesce()
    def failing_func():
        raise ValueError("Expected error")
        
    with pytest.raises(ValueError) as exc_info:
        failing_func()
        
    assert str(exc_info.value) == "Expected error"
    
def test_concurrent_exceptions():
    """Test that concurrent calls all receive the same exception."""
    @coalesce()
    def slow_failing_func():
        time.sleep(0.1)  # Small delay to ensure concurrent execution
        raise RuntimeError("Deliberate error")
        
    errors = []
    
    def thread_func():
        try:
            slow_failing_func()
            return None
        except Exception as e:
            return str(e)
            
    # Start threads
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(thread_func) for _ in range(3)]
        errors = [f.result() for f in futures]
        
    # All threads should get the same error
    assert errors == ["Deliberate error", "Deliberate error", "Deliberate error"]
    
def test_custom_key_function():
    """Test with a custom key function."""
    class KeyedFunction(object):
        def __init__(self):
            self.call_count = 0
            
        @coalesce(key_func=lambda x, *args, **kwargs: x)
        def __call__(self, x, y):
            self.call_count += 1
            time.sleep(0.1)  # Small delay to ensure concurrent execution
            return x + y
            
    keyed_func = KeyedFunction()
    results = []
    # These should coalesce because the key (first arg) is the same
    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(keyed_func, 1, 2)
        f2 = executor.submit(keyed_func, 1, 3)  # Different y, but same x
        results = [f1.result(), f2.result()]
        
    # Only one call should happen because keys are the same
    assert keyed_func.call_count == 1
    # First result should be from the actual execution (1+2)
    assert results[0] == 3
    # Second result should also be from the first execution (not 1+3)
    assert results[1] == 3
    
def test_future_reset():
    """Test that after completion, future is reset and function executes again."""
    class CountedFunction(object):
        def __init__(self):
            self.call_count = 0
            
        @coalesce()
        def __call__(self, x):
            self.call_count += 1
            time.sleep(0.1)  # Small delay to ensure concurrent execution
            return x * 2
            
    counted_func = CountedFunction()
        
    # First batch of concurrent calls
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(counted_func, 5) for _ in range(3)]
        results1 = [f.result() for f in futures]
        
    # Should have called function once
    assert counted_func.call_count == 1
    assert results1 == [10, 10, 10]
    
    # Second batch - should execute again since previous completed
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(counted_func, 5) for _ in range(3)]
        results2 = [f.result() for f in futures]
        
    # Should have called function a second time
    assert counted_func.call_count == 2
    assert results2 == [10, 10, 10]
