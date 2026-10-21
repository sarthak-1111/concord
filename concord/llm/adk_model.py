"""Google ADK model adapter: lets the forked ADK agents run on gpt-oss through concord's LLMClient."""
import asyncio
import json
import threading
import uuid
from typing import AsyncGenerator

from google.adk.models.base_llm import BaseLlm
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types
from pydantic import BaseModel, ValidationError

from concord.config import env
from concord.llm.client import LLMClient

_client: LLMClient | None = None
_client_lock = threading.Lock()


def shared_client() -> LLMClient:
    """One client per process, so the concurrency limit applies to every agent together."""
    global _client
    with _client_lock:
        if _client is None:
            _client = LLMClient.from_env()
    return _client


def _json_schema(schema: types.Schema | None) -> dict:
    if schema is None:
        return {"type": "object", "properties": {}}

    def fix(x):
        if isinstance(x, dict):
            out = {}
            for k, v in x.items():
                k = {"any_of": "anyOf", "max_items": "maxItems", "min_items": "minItems"}.get(k, k)
                out[k] = v.lower() if k == "type" and isinstance(v, str) else fix(v)
            return out
        return [fix(i) for i in x] if isinstance(x, list) else x
    return fix(schema.model_dump(mode="json", exclude_none=True))


def to_messages(llm_request: LlmRequest) -> list[dict]:
    msgs = []
    si = llm_request.config.system_instruction if llm_request.config else None
    if si:
        text = si if isinstance(si, str) else "".join(p.text or "" for p in getattr(si, "parts", []) or [])
        msgs.append({"role": "system", "content": text})
    for c in llm_request.contents:
        texts, calls = [], []
        for p in c.parts or []:
            if p.function_response:
                msgs.append({"role": "tool", "tool_name": p.function_response.name,
                             "content": json.dumps(p.function_response.response, default=str)})
            elif p.function_call:
                calls.append({"function": {"name": p.function_call.name, "arguments": p.function_call.args or {}}})
            elif p.text and not p.thought:
                texts.append(p.text)
        if texts or calls:
            m = {"role": "assistant" if c.role == "model" else "user", "content": "\n".join(texts)}
            if calls:
                m["tool_calls"] = calls
            msgs.append(m)
    return msgs


def to_tools(llm_request: LlmRequest) -> list[dict]:
    tools = []
    for t in (llm_request.config.tools or []) if llm_request.config else []:
        for fd in getattr(t, "function_declarations", None) or []:
            params = fd.parameters_json_schema if getattr(fd, "parameters_json_schema", None) else _json_schema(fd.parameters)
            tools.append({"type": "function", "function": {"name": fd.name, "description": fd.description or "", "parameters": params}})
    return tools


def _invalid_final_response(tool_calls: list[dict], llm_request: LlmRequest) -> str | None:
    """Validation error of a set_model_response call against the agent's output schema, if any."""
    final = llm_request.tools_dict.get("set_model_response")
    for tc in tool_calls:
        if tc["name"] == "set_model_response" and final is not None:
            try:
                final.output_schema.model_validate(tc["arguments"])
            except ValidationError as exc:
                return str(exc)[:400]
    return None


class ConcordLlm(BaseLlm):
    """ADK model backed by gpt-oss; `role` picks the thinking level from config.yaml."""
    model: str = "gpt-oss:120b"
    role: str = "tool_selection"

    async def generate_content_async(self, llm_request: LlmRequest, stream: bool = False) -> AsyncGenerator[LlmResponse, None]:
        schema = llm_request.config.response_schema if llm_request.config else None
        if not (isinstance(schema, type) and issubclass(schema, BaseModel)):
            schema = None
        tools = to_tools(llm_request)
        msgs = to_messages(llm_request)
        result = await asyncio.to_thread(shared_client().chat, self.role, msgs, schema=schema, tools=tools or None)
        if err := _invalid_final_response(result.tool_calls, llm_request):
            # one repair attempt, same rule as the client's schema validation; ADK would raise otherwise
            msgs = msgs + [{"role": "assistant", "content": "", "tool_calls": [{"function": {"name": tc["name"], "arguments": tc["arguments"]}} for tc in result.tool_calls]},
                           {"role": "tool", "tool_name": "set_model_response",
                            "content": f"Rejected, the arguments do not match the schema: {err}. If you have not called the task tools yet, "
                                       "call them first; then call set_model_response with every required field."}]
            result = await asyncio.to_thread(shared_client().chat, self.role, msgs, schema=schema, tools=tools or None)
        parts = [types.Part(function_call=types.FunctionCall(id=f"call_{uuid.uuid4().hex[:12]}", name=tc["name"], args=tc["arguments"]))
                 for tc in result.tool_calls]
        if result.data is not None and isinstance(result.data, BaseModel):
            parts.append(types.Part(text=result.data.model_dump_json()))
        elif result.content and not result.tool_calls:
            parts.append(types.Part(text=result.content))
        yield LlmResponse(content=types.Content(role="model", parts=parts),
                          usage_metadata=types.GenerateContentResponseUsageMetadata(
                              prompt_token_count=result.prompt_tokens, candidates_token_count=result.completion_tokens))


def model_for(role: str) -> ConcordLlm:
    return ConcordLlm(model=env().get("LLM_MODEL", "gpt-oss:120b"), role=role)
