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
- Works with both synchronous and threaded code
- Supports custom key functions for controlling how calls are grouped
- Compatible with Python 2.7+ and Python 3.x
- No external dependencies

## Usage

### Basic Usage

```python
from concurrent_coalesce import coalesce

@coalesce()
def fetch_data(user_id):
    print("Fetching data for user", user_id)
    response = requests.get("https://api.example.com/users", params={"user_id": user_id})
    response.raise_for_status()
    return response.json()
```

When multiple threads call `fetch_data()` with the same `user_id` concurrently, only one thread will actually execute the function. All other threads will wait for the result and receive the same return value.

### Custom Key Function

You can customize how arguments are grouped by providing a key function:

```python
@coalesce(key_func=lambda user_id, **kwargs: user_id)
def fetch_user_data(user_id, include_history=False, include_preferences=True):
    # This will coalesce based only on user_id, ignoring other parameters
    response = requests.get("https://api.example.com/users", params={
        "user_id": user_id,
        "include_history": include_history,
        "include_preferences": include_preferences
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

The decorator can be used in four ways:
1. As a decorator `@coalesce()`
2. As a decorator with key function: `@coalesce(key_func=my_key_func)`
3. As a direct function call: `coalesce(my_function)`
4. As a direct function call with key function: `coalesce(my_function, key_func=my_key_func)`

**Parameters:**
- `key_func`: Optional callable that takes `*args, **kwargs` and returns a hashable key.
  Defaults to using `(args, frozenset(kwargs.items()))`.
- `*args`: If provided, must be a single callable that will be decorated.
  If no args are provided, returns the decorator function.
  If multiple args are provided, raises TypeError.

**Raises:**
- `TypeError`: If key_func is not callable or if multiple arguments are provided in *args

## License

MIT License
