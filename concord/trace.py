"""Append-only JSONL trace of a run: tool calls, LLM calls (tokens, latency), checks, critic rounds."""
import json
import threading
import time
from contextvars import ContextVar
from pathlib import Path


class Trace:
    def __init__(self, path: str | Path | None = None):
        self.path = Path(path) if path else None
        self.events: list[dict] = []
        self._lock = threading.Lock()
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, kind: str, **fields) -> dict:
        event = {"ts": round(time.time(), 3), "kind": kind, **fields}
        with self._lock:
            self.events.append(event)
            if self.path:
                with self.path.open("a") as f:
                    f.write(json.dumps(event, default=str) + "\n")
        return event

    def totals(self) -> dict:
        calls = [e for e in self.events if e["kind"] == "llm_call"]
        return {
            "llm_calls": len(calls),
            "prompt_tokens": sum(e.get("prompt_tokens", 0) for e in calls),
            "completion_tokens": sum(e.get("completion_tokens", 0) for e in calls),
            "llm_seconds": round(sum(e.get("latency_s", 0) for e in calls), 2),
        }


# The trace of the run in progress; contextvars follow asyncio tasks and asyncio.to_thread.
CURRENT_TRACE: ContextVar[Trace | None] = ContextVar("concord_trace", default=None)
