from __future__ import print_function
import threading
import functools
import sys

if sys.version_info >= (3, 5):
    import asyncio
    def iscoroutinefunction(func):
        return asyncio.iscoroutinefunction(func)
    ASYNC_SUPPORTED = True
else:
    def iscoroutinefunction(func):
        return False
    ASYNC_SUPPORTED = False

try:
    from concurrent.futures import Future
except ImportError:
    class Future:
        """A minimal implementation of a Future object that mimics concurrent.futures.Future."""
        def __init__(self):
            self._condition = threading.Condition()
            self._result = None
            self._exception = None
            self._done = False
            
        def done(self):
            """Return True if the future is done."""
            with self._condition:
                return self._done
                
        def set_result(self, result):
            """Set the result of the future."""
            with self._condition:
                self._result = result
                self._done = True
                self._condition.notify_all()
                
        def set_exception(self, exception):
            """Set an exception for the future."""
            with self._condition:
                self._exception = exception
                self._done = True
                self._condition.notify_all()
                
        def result(self):
            """Return the result of the future, blocking if necessary."""
            with self._condition:
                while not self._done:
                    self._condition.wait()
                if self._exception:
                    raise self._exception
                return self._result

def coalesce(key_func=None, *args):
    """
    A decorator that coalesces concurrent calls to a function with the same arguments into a single execution.
    
    This decorator ensures that multiple concurrent calls to the decorated function with identical arguments
    will only execute the function once, with all callers receiving the same result object. This is useful for
    preventing duplicate work when multiple threads or coroutines attempt to perform the same operation simultaneously.
    If you need to modify the result object, consider creating a copy first to avoid affecting other callers.
    
    The decorator works with both synchronous functions and coroutines (Python 3.5+):
    
    # Using with synchronous functions:
    @coalesce()
    def fetch_data(user_id):
        response = requests.get("https://api.example.com/users", params={"user_id": user_id})
        return response.json()
    
    # Using with async/await (Python 3.5+):
    @coalesce()
    async def fetch_data(user_id):
        response = await aiohttp.get("https://api.example.com/users", params={"user_id": user_id})
        return await response.json()
    
    The coalescing is based on a key derived from the function arguments. By default, the key is created
    from the positional and keyword arguments, but a custom key function can be provided to control how
    calls are grouped or when arguments are non-hashable.
    
    The decorator can be used in two ways:
    1. As a decorator `@coalesce()`
    2. As a direct function call: `coalesce(my_function)`
    
    Returns:
        A decorator function that wraps the target function with coalescing behavior.
        For synchronous functions, returns the result directly.
        For coroutines (Python 3.5+), returns an asyncio.Task that can be awaited.

    Args:
        key_func: Optional function that takes *args, **kwargs and returns a hashable key.
                 Defaults to using (tuple(args), frozenset(kwargs.items()))
        *args: If provided, must be a single callable that will be decorated.
               If no args are provided, returns the decorator function.
               If multiple args are provided, raises TypeError.

    Raises:
        TypeError: If key_func is not callable or if multiple arguments are provided in *args
    """

    # Default key function if none is provided
    if key_func is None:
        key_func = lambda *args, **kwargs: (tuple(args), frozenset(kwargs.items()))

    # Validate that key_func is callable
    if not callable(key_func):
        raise TypeError("key_func must be callable or None")
        
    def decorator(func):
        lock = threading.Lock()
        tasks = {}

        if iscoroutinefunction(func):
            if not ASYNC_SUPPORTED:
                raise RuntimeError("Async requires Python 3.5+")                    
            
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                key = key_func(*args, **kwargs)
                with lock:
                    if key not in tasks or tasks[key].done():
                        task = asyncio.Task(func(*args, **kwargs))

                        def cleanup_task(task):
                            with lock:
                                if tasks.get(key, None) is task:
                                    del tasks[key]
                        task.add_done_callback(cleanup_task)
                        
                        tasks[key] = task
                    else:
                        task = tasks[key]
                return task
        
        else:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                key = key_func(*args, **kwargs)
                is_master = False
                with lock:
                    if key not in tasks or tasks[key].done():
                        tasks[key] = Future()
                        is_master = True
                    future = tasks[key]

                if is_master:
                    try:
                        result = func(*args, **kwargs)
                        with lock:
                            if key in tasks and tasks[key] is future:
                                future.set_result(result)
                                del tasks[key]
                    except Exception as e:
                        with lock:
                            if key in tasks and tasks[key] is future:
                                future.set_exception(e)
                                del tasks[key]

                return future.result()
        return wrapper
    
    # If called directly with a function, apply the decorator
    if len(args) == 0:
        return decorator
    elif len(args) == 1 and callable(args[0]):
        return decorator(args[0])
    else:
        raise TypeError("Invalid number of arguments")
