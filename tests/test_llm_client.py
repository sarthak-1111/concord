import json

import pytest
import requests
from pydantic import BaseModel

from concord.llm.client import EndpointDown, LLMClient, LLMError
from concord.trace import Trace

CFG = {"think": {"critic": "high"}, "timeout_s": {"low": 1, "medium": 1, "high": 1},
       "max_retries": 2, "backoff_s": 0.0, "max_concurrency": 2}
KEY = "test-key-should-never-leak-0123456789"


class FakeResponse:
    def __init__(self, payload, status=200):
        self.payload, self.status_code, self.text = payload, status, json.dumps(payload)

    def json(self):
        return self.payload

    def iter_lines(self):  # streamed reply: content split over two chunks, counts on the final one
        m = self.payload.get("message", {})
        text = m.get("content", "")
        yield json.dumps({"message": {**m, "content": text[: len(text) // 2]}, "done": False}).encode()
        yield json.dumps({**self.payload, "message": {"role": "assistant", "content": text[len(text) // 2:]}, "done": True}).encode()


class FakeSession:
    """Replays queued replies; an Exception instance in the queue is raised instead."""

    def __init__(self, replies):
        self.replies, self.bodies = list(replies), []

    def post(self, url, json=None, timeout=None, headers=None, stream=False):
        assert headers["Authorization"] == f"Bearer {KEY}"
        self.bodies.append(json)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return reply


def msg(content, **extra):
    return FakeResponse({"message": {"role": "assistant", "content": content, **extra},
                         "prompt_eval_count": 10, "eval_count": 5})


def client(replies, caps=None):
    c = LLMClient("https://example.test/", KEY, "gpt-oss:120b", cfg=CFG, trace=Trace(), session=FakeSession(replies))
    c.caps = caps or {"tools": True, "format": True}
    return c


class Verdict(BaseModel):
    verdict: str
    score: float


def test_retries_then_succeeds_and_uses_role_thinking():
    c = client([requests.ConnectionError("boom"), FakeResponse({}, status=503), msg("OK")])
    assert c.chat("critic", [{"role": "user", "content": "hi"}]).content == "OK"
    assert c.http.bodies[-1]["think"] == "high"
    assert [e["kind"] for e in c.trace.events].count("llm_retry") == 2


class CutStream(FakeResponse):
    def iter_lines(self):  # the tunnel drops the connection mid-reply
        yield json.dumps({"message": {"role": "assistant", "content": "O"}, "done": False}).encode()
        raise requests.exceptions.ChunkedEncodingError("Connection broken: IncompleteRead")


def test_stream_cut_midway_is_retried():
    c = client([CutStream({}), msg("OK")])
    assert c.chat("critic", [{"role": "user", "content": "hi"}]).content == "OK"
    assert [e["error"] for e in c.trace.events if e["kind"] == "llm_retry"] == ["ChunkedEncodingError"]


def test_endpoint_down_is_clear():
    c = client([requests.ConnectionError("x")] * 3)
    with pytest.raises(EndpointDown, match="LLM_BASE_URL"):
        c.chat("summary", [{"role": "user", "content": "hi"}])


def test_native_schema_with_one_repair():
    c = client([msg("not json"), msg('{"verdict": "pass", "score": 0.9}')])
    r = c.chat("critic", [{"role": "user", "content": "judge"}], schema=Verdict)
    assert r.data == Verdict(verdict="pass", score=0.9)
    assert "format" in c.http.bodies[0] and len(c.http.bodies) == 2


def test_schema_failure_after_repair_raises():
    c = client([msg("nope"), msg("still nope")])
    with pytest.raises(LLMError, match="after one repair"):
        c.chat("critic", [{"role": "user", "content": "judge"}], schema=Verdict)


def test_json_in_text_fallback_when_no_native_support():
    c = client([msg('```json\n{"verdict": "warn", "score": 0.5}\n```'),
                msg('{"tool_calls": [{"name": "fit_pdf", "arguments": {"rmax": 20}}]}')],
               caps={"tools": False, "format": False})
    r = c.chat("critic", [{"role": "user", "content": "judge"}], schema=Verdict)
    assert r.data.verdict == "warn" and "format" not in c.http.bodies[0]
    assert c.http.bodies[0]["messages"][0]["role"] == "system"
    tools = [{"type": "function", "function": {"name": "fit_pdf", "parameters": {"type": "object"}}}]
    r = c.chat("tool_selection", [{"role": "user", "content": "fit"}], tools=tools)
    assert r.tool_calls == [{"name": "fit_pdf", "arguments": {"rmax": 20}}]


def test_native_tool_calls_parsed():
    c = client([msg("", tool_calls=[{"function": {"name": "fit_pdf", "arguments": {"rmax": 20}}}])])
    r = c.chat("tool_selection", [{"role": "user", "content": "fit"}], tools=[{"type": "function", "function": {"name": "fit_pdf"}}])
    assert r.tool_calls == [{"name": "fit_pdf", "arguments": {"rmax": 20}}]


def test_probe_detects_capabilities():
    c = client([msg("", tool_calls=[{"function": {"name": "get_answer", "arguments": {"x": 1}}}]), msg('{"ok": true}')])
    c.caps = None
    assert c.capabilities() == {"tools": True, "format": True}


def test_key_never_in_trace_or_repr():
    c = client([msg("OK")])
    c.chat("summary", [{"role": "user", "content": "hi"}])
    assert KEY not in repr(c) and KEY not in json.dumps(c.trace.events)
    assert c.trace.totals()["prompt_tokens"] == 10
