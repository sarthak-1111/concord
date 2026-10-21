"""Client for the Ollama-style chat endpoint behind a bearer token (one model, gpt-oss, for every role).

- thinking level per role and timeout per level from config.yaml
- retries with exponential backoff; EndpointDown with a clear message when the server is gone
- startup probe for native tool calls (`tools`) and JSON-schema output (`format`);
  falls back to JSON-in-text with schema validation and one repair attempt
- at most `max_concurrency` requests in flight (the semaphore queues the rest)
- tokens and latency per call go to the trace; the key never does
"""
import json
import re
import threading
import time
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import requests
from pydantic import BaseModel, ValidationError

from concord.config import env, settings
from concord.trace import CURRENT_TRACE, Trace


class LLMError(RuntimeError):
    pass


class EndpointDown(LLMError):
    pass


class _Retryable(Exception):
    pass


@dataclass
class ChatResult:
    content: str
    tool_calls: list[dict] = field(default_factory=list)
    data: Any = None
    thinking: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0


class LLMClient:
    def __init__(self, base_url: str, api_key: str, model: str, cfg: dict | None = None,
                 trace: Trace | None = None, session: requests.Session | None = None):
        cfg = cfg or settings()["llm"]
        self.base_url = base_url.rstrip("/")
        self.host = urlparse(self.base_url).netloc
        self._api_key = api_key
        self.model = model
        self.think = cfg["think"]
        self.timeout_s = cfg["timeout_s"]
        self.max_retries = cfg["max_retries"]
        self.backoff_s = cfg["backoff_s"]
        self._slots = threading.BoundedSemaphore(cfg["max_concurrency"])
        self._probe_lock = threading.Lock()
        self.trace = trace or Trace()
        self.http = session or requests.Session()
        self.caps: dict | None = None

    @classmethod
    def from_env(cls, trace: Trace | None = None) -> "LLMClient":
        e = env()
        missing = [k for k in ("LLM_BASE_URL", "LLM_API_KEY") if k not in e]
        if missing:
            raise LLMError(f"Missing {', '.join(missing)} in .env (see .env.example)")
        return cls(e["LLM_BASE_URL"], e["LLM_API_KEY"], e.get("LLM_MODEL", "gpt-oss:120b"), trace=trace)

    def __repr__(self) -> str:
        return f"LLMClient(model={self.model!r}, host={self.host!r})"

    def _trace(self) -> Trace:
        return CURRENT_TRACE.get() or self.trace

    # -- transport -------------------------------------------------------------------------
    def _post(self, body: dict, level: str, role: str) -> tuple[dict, float]:
        last: Exception | None = None
        for attempt in range(self.max_retries + 1):
            t0 = time.time()
            try:
                with self._slots:
                    r = self.http.post(f"{self.base_url}/api/chat", json=body, timeout=(15, self.timeout_s[level]),
                                       headers={"Authorization": f"Bearer {self._api_key}"}, stream=bool(body.get("stream")))
                    if r.status_code == 429 or r.status_code >= 500:
                        raise _Retryable(f"HTTP {r.status_code}")
                    if r.status_code >= 400:
                        raise LLMError(f"LLM endpoint returned HTTP {r.status_code}: {r.text[:200]}")
                    data = self._collect(r, t0, self.timeout_s[level]) if body.get("stream") else r.json()
                return data, time.time() - t0
            except (requests.ConnectionError, requests.Timeout, _Retryable) as exc:
                last = exc
                # HTTP status only: connection errors embed the endpoint URL, which counts as a secret here
                self._trace().log("llm_retry", role=role, attempt=attempt + 1, error=str(exc) if isinstance(exc, _Retryable) else type(exc).__name__)
                if attempt < self.max_retries:
                    time.sleep(self.backoff_s * 2 ** attempt)
        raise EndpointDown(f"LLM endpoint {self.host} not responding after {self.max_retries + 1} attempts "
                           f"({type(last).__name__}: {str(last)[:120]}). The URL can change between sessions: "
                           f"check LLM_BASE_URL in .env.")

    @staticmethod
    def _collect(r, t0: float, limit: float) -> dict:
        """Merge a streamed /api/chat reply (NDJSON chunks) into the non-streamed shape. Streaming keeps bytes moving
        through proxies that cut idle requests (Cloudflare tunnels close after 100 s without data)."""
        msg = {"role": "assistant", "content": "", "thinking": ""}
        last: dict = {}
        for line in r.iter_lines():
            if time.time() - t0 > limit:
                raise requests.Timeout(f"no complete reply within {limit} s")
            if not line:
                continue
            last = json.loads(line)
            if "error" in last:
                raise _Retryable(f"stream error: {str(last['error'])[:80]}")
            m = last.get("message", {})
            msg["content"] += m.get("content") or ""
            msg["thinking"] += m.get("thinking") or ""
            if m.get("tool_calls"):
                msg.setdefault("tool_calls", []).extend(m["tool_calls"])
        if not last.get("done"):
            raise _Retryable("stream ended before done")
        return {**last, "message": msg}

    # -- capability probe ------------------------------------------------------------------
    def capabilities(self) -> dict:
        with self._probe_lock:
            if self.caps is None:
                self.caps = self.probe()
        return self.caps

    def probe(self) -> dict:
        caps = {"tools": False, "format": False}
        base = {"model": self.model, "think": "low", "stream": False}
        tool = {"type": "function", "function": {
            "name": "get_answer", "description": "Returns the answer for x.",
            "parameters": {"type": "object", "properties": {"x": {"type": "integer"}}, "required": ["x"]}}}
        try:
            resp, _ = self._post({**base, "tools": [tool],
                                  "messages": [{"role": "user", "content": "Call get_answer with x=1."}]}, "low", "probe")
            caps["tools"] = bool(resp.get("message", {}).get("tool_calls"))
        except EndpointDown:
            raise
        except LLMError:
            pass
        schema = {"type": "object", "properties": {"ok": {"type": "boolean"}}, "required": ["ok"]}
        try:
            resp, _ = self._post({**base, "format": schema,
                                  "messages": [{"role": "user", "content": "Is water wet? Answer as JSON."}]}, "low", "probe")
            caps["format"] = isinstance(json.loads(resp["message"]["content"]).get("ok"), bool)
        except EndpointDown:
            raise
        except (LLMError, ValueError, KeyError, AttributeError, TypeError):
            pass
        self._trace().log("llm_probe", host=self.host, model=self.model, **caps)
        return caps

    def health(self) -> dict:
        t0 = time.time()
        r = self.chat("summary", [{"role": "user", "content": "Reply with exactly: OK"}])
        return {"ok": "OK" in r.content, "latency_s": round(time.time() - t0, 2), "model": self.model,
                "host": self.host, **{f"native_{k}": v for k, v in self.capabilities().items()}}

    # -- chat ------------------------------------------------------------------------------
    def chat(self, role: str, messages: list[dict], *, schema: type[BaseModel] | dict | None = None,
             tools: list[dict] | None = None, think: str | None = None) -> ChatResult:
        level = think or self.think.get(role, "low")
        caps = self.capabilities()
        json_schema = schema.model_json_schema() if isinstance(schema, type) else schema
        msgs = list(messages)
        body: dict = {"model": self.model, "think": level, "stream": True}
        if tools:
            if caps["tools"]:
                body["tools"] = tools
            else:
                msgs = [_system(TOOLS_IN_TEXT.format(tools=json.dumps(tools)))] + msgs
        if json_schema is not None:
            if caps["format"]:
                body["format"] = json_schema
            else:
                msgs = [_system(SCHEMA_IN_TEXT.format(schema=json.dumps(json_schema)))] + msgs
        result = self._call(body, msgs, level, role)
        if tools and not caps["tools"]:
            result.tool_calls = _inline_tool_calls(result.content)
        if json_schema is not None:
            result.data, err = _validate(result.content, schema)
            if err:
                msgs = msgs + [{"role": "assistant", "content": result.content},
                               {"role": "user", "content": f"That reply did not match the required JSON schema: {err}. "
                                                           "Reply again with only the corrected JSON object."}]
                result = self._call(body, msgs, level, role, repair=True)
                result.data, err = _validate(result.content, schema)
                if err:
                    raise LLMError(f"{role}: reply failed schema validation after one repair attempt: {err}")
        return result

    def _call(self, body: dict, msgs: list[dict], level: str, role: str, repair: bool = False) -> ChatResult:
        resp, latency = self._post({**body, "messages": msgs}, level, role)
        msg = resp.get("message") or {}
        result = ChatResult(
            content=msg.get("content") or "",
            tool_calls=[{"name": tc["function"]["name"], "arguments": tc["function"].get("arguments") or {}}
                        for tc in msg.get("tool_calls") or []],
            thinking=msg.get("thinking") or "",
            prompt_tokens=resp.get("prompt_eval_count", 0),
            completion_tokens=resp.get("eval_count", 0),
            latency_s=round(latency, 3),
        )
        self._trace().log("llm_call", role=role, think=level, model=self.model, latency_s=result.latency_s,
                       prompt_tokens=result.prompt_tokens, completion_tokens=result.completion_tokens,
                       repair=repair, tool_calls=[t["name"] for t in result.tool_calls],
                       preview=result.content[:160])
        return result


TOOLS_IN_TEXT = ("You can call these tools (JSON schema): {tools}\n"
                 "To call tools, reply with only JSON: {{\"tool_calls\": [{{\"name\": \"...\", \"arguments\": {{...}}}}]}}. "
                 "Otherwise reply normally.")
SCHEMA_IN_TEXT = "Reply with only a JSON object that matches this JSON schema, no prose: {schema}"


def _system(text: str) -> dict:
    return {"role": "system", "content": text}


def _extract_json(text: str) -> Any:
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text)
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        if start == -1 or end <= start:
            raise
        return json.loads(text[start:end + 1])


def _validate(text: str, schema: type[BaseModel] | dict) -> tuple[Any, str | None]:
    try:
        data = _extract_json(text)
    except ValueError as exc:
        return None, f"not valid JSON ({exc})"
    if isinstance(schema, type):
        try:
            return schema.model_validate(data), None
        except ValidationError as exc:
            return None, str(exc)[:500]
    missing = [k for k in schema.get("required", []) if not isinstance(data, dict) or k not in data]
    return (None, f"missing required keys {missing}") if missing else (data, None)


def _inline_tool_calls(text: str) -> list[dict]:
    try:
        data = _extract_json(text)
    except ValueError:
        return []
    calls = data.get("tool_calls") if isinstance(data, dict) else None
    return [{"name": c["name"], "arguments": c.get("arguments") or {}} for c in calls or [] if "name" in c]


if __name__ == "__main__":  # live health check: `uv run python -m concord.llm.client`
    print(json.dumps(LLMClient.from_env().health(), indent=2))
