import pytest
import asyncio
import sys
from concurrent_coalesce import coalesce

pytestmark = pytest.mark.asyncio

async def test_async_basic_functionality():
    """Test that the decorated async function returns the correct result."""
    class AsyncAddFunction:
        def __init__(self):
            self.call_count = 0
            
        @coalesce()
        async def __call__(self, a, b):
            self.call_count += 1
            await asyncio.sleep(0.1)  # Simulate async work
            return a + b
            
    add_func = AsyncAddFunction()
    result = await add_func(2, 3)
    assert result == 5
    assert add_func.call_count == 1
    
    # Call again with same args - should increment counter
    result = await add_func(2, 3)
    assert result == 5
    assert add_func.call_count == 2

async def test_async_concurrency_same_args():
    """Test that concurrent async calls with same arguments only execute once."""
    class AsyncSlowFunction:
        def __init__(self):
            self.call_count = 0
            
        @coalesce()
        async def __call__(self, x):
            self.call_count += 1
            await asyncio.sleep(0.1)  # Simulate async work
            return x * 2
            
    slow_func = AsyncSlowFunction()
    
    # Create multiple concurrent tasks
    tasks = [slow_func(5) for _ in range(5)]
    results = await asyncio.gather(*tasks)
    
    # All results should be the same
    assert results == [10, 10, 10, 10, 10]
    assert slow_func.call_count == 1

async def test_async_concurrency_different_args():
    """Test that concurrent async calls with different arguments execute separately."""
    class AsyncParameterizedFunction:
        def __init__(self):
            self.call_counts = {}
            
        @coalesce()
        async def __call__(self, key):
            self.call_counts[key] = self.call_counts.get(key, 0) + 1
            await asyncio.sleep(0.1)  # Simulate async work
            return f"result-{key}"
            
    parameterized_func = AsyncParameterizedFunction()
    
    # Run 10 tasks with 5 different values (2 tasks per value)
    args = [1, 2, 3, 4, 5, 1, 2, 3, 4, 5]
    tasks = [parameterized_func(arg) for arg in args]
    results = await asyncio.gather(*tasks)
    
    # Check that each unique argument was processed once
    assert parameterized_func.call_counts == {1: 1, 2: 1, 3: 1, 4: 1, 5: 1}
    
    # Verify results
    expected_results = [f"result-{arg}" for arg in args]
    assert results == expected_results

async def test_async_exception_handling():
    """Test that exceptions are properly propagated in async functions."""
    @coalesce()
    async def failing_func():
        await asyncio.sleep(0.1)  # Simulate async work
        raise ValueError("Expected error")
        
    with pytest.raises(ValueError) as exc_info:
        await failing_func()
        
    assert str(exc_info.value) == "Expected error"

async def test_async_concurrent_exceptions():
    """Test that concurrent async calls all receive the same exception."""
    @coalesce()
    async def slow_failing_func():
        await asyncio.sleep(0.1)  # Simulate async work
        raise RuntimeError("Deliberate error")
        
    async def task_func():
        try:
            await slow_failing_func()
            return None
        except Exception as e:
            return str(e)
            
    # Create multiple concurrent tasks
    tasks = [task_func() for _ in range(3)]
    errors = await asyncio.gather(*tasks)
    
    # All tasks should get the same error
    assert errors == ["Deliberate error", "Deliberate error", "Deliberate error"]

async def test_async_custom_key_function():
    """Test with a custom key function in async context."""
    class AsyncKeyedFunction:
        def __init__(self):
            self.call_count = 0
            
        @coalesce(key_func=lambda x, *args, **kwargs: x)
        async def __call__(self, x, y):
            self.call_count += 1
            await asyncio.sleep(0.1)  # Simulate async work
            return x + y
            
    keyed_func = AsyncKeyedFunction()
    
    # These should coalesce because the key (first arg) is the same
    task1 = keyed_func(1, 2)
    task2 = keyed_func(1, 3)  # Different y, but same x
    results = await asyncio.gather(task1, task2)
    
    # Only one call should happen because keys are the same
    assert keyed_func.call_count == 1
    # First result should be from the actual execution (1+2)
    assert results[0] == 3
    # Second result should also be from the first execution (not 1+3)
    assert results[1] == 3

async def test_async_future_reset():
    """Test that after completion, future is reset and async function executes again."""
    class AsyncCountedFunction:
        def __init__(self):
            self.call_count = 0
            
        @coalesce()
        async def __call__(self, x):
            self.call_count += 1
            await asyncio.sleep(0.1)  # Simulate async work
            return x * 2
            
    counted_func = AsyncCountedFunction()
    
    # First batch of concurrent calls
    tasks1 = [counted_func(5) for _ in range(3)]
    results1 = await asyncio.gather(*tasks1)
    
    # Should have called function once
    assert counted_func.call_count == 1
    assert results1 == [10, 10, 10]
    
    # Second batch - should execute again since previous completed
    tasks2 = [counted_func(5) for _ in range(3)]
    results2 = await asyncio.gather(*tasks2)
    
    # Should have called function a second time
    assert counted_func.call_count == 2
    assert results2 == [10, 10, 10]

if (3, 5) <= sys.version_info <= (3, 10):
    async def test_coroutine_decorator_style():
        """Test that coalesce works with the older @asyncio.coroutine decorator style."""
        class CoroutineStyleFunction:
            def __init__(self):
                self.call_count = 0
                
            @coalesce()
            @asyncio.coroutine
            def __call__(self, x):
                self.call_count += 1
                yield from asyncio.sleep(0.1)  # Simulate async work
                return x * 3
                
        coro_func = CoroutineStyleFunction()
        
        # Test single call
        result = await coro_func(4)
        assert result == 12
        assert coro_func.call_count == 1
        
        # Test concurrent calls
        tasks = [coro_func(4) for _ in range(3)]
        results = await asyncio.gather(*tasks)
        
        # All results should be the same and function should only be called once
        assert results == [12, 12, 12]
        assert coro_func.call_count == 2  # Once for single call, once for concurrent calls
