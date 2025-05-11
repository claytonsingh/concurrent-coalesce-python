# Concurrent Coalesce

A Python decorator that coalesces concurrent function calls.

## Description

This package provides a decorator that helps manage concurrent function calls by coalescing them, preventing redundant executions when multiple calls occur simultaneously.

## Installation

```bash
pip install concurrent-coalesce
```

## Features

- Prevents redundant concurrent execution of functions with identical arguments
- Works with both synchronous threads and asynchronous code (Python 3.5+)
- Supports custom key functions for unhashable inputs and controlling how calls are grouped
- Compatible with Python 2.7 and Python 3.5+
- No external dependencies

## Usage

See [examples](https://github.com/claytonsingh/concurrent-coalesce-python/tree/master/examples)

### Basic Usage

```python
from concurrent_coalesce import coalesce

# Synchronous usage
@coalesce()
def fetch_data(user_id):
    print("Fetching data for user", user_id)
    response = requests.get("https://api.example.com/users", params={"user_id": user_id})
    response.raise_for_status()
    return response.json()
```

When multiple threads call `fetch_data()` with the same `user_id` concurrently, only one will actually execute the function. All others will wait for the result and receive the same return value.

### Async Usage

Async support requires Python 3.5+

```python
from concurrent_coalesce import coalesce

# Async usage (Python 3.5+)
@coalesce()
async def fetch_data_async(user_id):
    print("Fetching data for user", user_id)
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com/users", params={"user_id": user_id}) as response:
            response.raise_for_status()
            return await response.json()
```

When multiple coroutines call `fetch_data_async()` with the same `user_id` concurrently, only one will actually execute the function. All others will wait for the result and receive the same return value.

### Custom Key Function

The primary purpose of `key_func` is to handle unhashable inputs. By default, the decorator uses the function arguments as a key, which requires them to be hashable. When your function receives unhashable arguments (like lists or dictionaries), you can use `key_func` to convert them into hashable values.

You can also use `key_func` to customize how arguments are grouped for coalescing:

```python
# user_ids is a list (unhashable), so we convert it to a sorted tuple (hashable)
# This ensures that [1, 2] and [2, 1] are treated as the same request
@coalesce(key_func=lambda user_ids, **kwargs: tuple(sorted(user_ids)))
def fetch_multiple_users(user_ids, include_history=False):
    response = requests.get("https://api.example.com/users", params={
        "user_ids": user_ids,
        "include_history": include_history
    })
    response.raise_for_status()
    return response.json()
```

## How It Works

The `coalesce` decorator:

1. Intercepts function calls and generates a key based on the function arguments
2. For the first call with a given key, the function executes normally
3. Subsequent calls with the same key (before the first call completes) wait for the result
4. All callers receive the same return value or exception
5. After completion, the next call will trigger a new execution

For synchronous functions, the result is returned directly. For coroutines (Python 3.5+), an asyncio.Task is returned that can be awaited.

```mermaid
sequenceDiagram
  autonumber
  participant T1 as Thread 1
  participant T2 as Thread 2
  participant C as Decorator
  participant F as fetch_data()

  T1 ->> F : Call to fetch_data()
  activate C
  activate F
  T2 ->> C : Call to fetch_data()
  Note right of C: Thread 2 is blocked while<br/>Thread 1 processes fetch_data()
  F ->> T1 : Return from fetch_data()
  deactivate F
  C ->> T2 : Return from fetch_data()
  deactivate C
```

## API Reference

### `@coalesce(key_func=None, *args)`

A decorator that coalesces concurrent calls to a function with the same arguments.

The decorator can be used in two ways:
1. As a decorator `@coalesce()`
2. As a direct function call: `coalesce(my_function)`

**Parameters:**
- `key_func`: Optional callable that takes `*args, **kwargs` and returns a hashable key.
  Defaults to using `(tuple(args), frozenset(kwargs.items()))`.
- `*args`: If provided, must be a single callable that will be decorated.
  If no args are provided, returns the decorator function.
  If multiple args are provided, raises TypeError.

**Returns:**
- For synchronous functions: The result of the function call
- For coroutines (Python 3.5+): An asyncio.Task that can be awaited

**Raises:**
- `TypeError`: If key_func is not callable or if multiple arguments are provided in *args

## License

[MIT License](https://github.com/claytonsingh/concurrent-coalesce-python/blob/master/LICENSE)
