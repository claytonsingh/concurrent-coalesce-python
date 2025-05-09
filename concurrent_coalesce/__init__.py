from concurrent_coalesce.core import coalesce, ASYNC_SUPPORTED
import sys

if sys.version_info.major == 2:
    try:
        import pkg_resources
        __version__ = pkg_resources.get_distribution("concurrent-coalesce").version
    except Exception:
        __version__ = "0.0.0"
else:
    try:
        from importlib.metadata import version
        __version__ = version("concurrent-coalesce")
    except Exception:
        __version__ = "0.0.0"
