"""Deterministic analysis tools. Every scientific number Concord reports comes out of a function registered here.

The common interface: a tool is a plain typed function, registered with @tool, that never calls an LLM.
Calls are timed and logged to the current run trace; exceptions propagate to the caller.
"""
import functools
import time

from concord.trace import CURRENT_TRACE

TOOLS: dict = {}


def tool(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        t0, ok, err = time.time(), True, None
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            ok, err = False, f"{type(exc).__name__}: {exc}"
            raise
        finally:
            if (trace := CURRENT_TRACE.get()) is not None:
                trace.log("tool_call", tool=fn.__name__, ok=ok, error=err, seconds=round(time.time() - t0, 3))

    TOOLS[fn.__name__] = wrapper
    return wrapper
