"""Smoke test: the forked CrystaLenz XRD agent pipeline (Google ADK) running on gpt-oss via concord's adapter."""
import asyncio
import sys
import time
from pathlib import Path

from google.adk.runners import InMemoryRunner
from google.genai import types

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # the forked agents import as `src.*`, like backend/app/main.py

from concord.trace import CURRENT_TRACE, Trace  # noqa: E402
from src.agents.xrd_agent.agent import xrd_specialist_agent  # noqa: E402


async def main(path: str) -> int:
    trace = Trace(ROOT / "runs" / "fork_smoke.jsonl")
    CURRENT_TRACE.set(trace)
    runner = InMemoryRunner(agent=xrd_specialist_agent, app_name="CrystaLens")
    session = await runner.session_service.create_session(app_name="CrystaLens", user_id="smoke")
    prompt = f"Analyse the XRD data in {path}. Wavelength is Cu K-alpha 1.5406 A."
    t0, calls = time.time(), []
    async for event in runner.run_async(user_id="smoke", session_id=session.id,
                                        new_message=types.Content(role="user", parts=[types.Part(text=prompt)])):
        for part in (event.content.parts if event.content else []) or []:
            if part.function_call:
                calls.append(part.function_call.name)
                print(f"[{event.author}] call {part.function_call.name}")
            elif part.function_response:
                resp = part.function_response.response or {}
                print(f"[{event.author}] {part.function_response.name} -> success={resp.get('success')} {str(resp.get('message', ''))[:100]}")
    print(f"done in {time.time() - t0:.0f}s, tools called: {calls}, llm: {trace.totals()}")
    return 0 if "find_and_fit_peaks" in calls and "scherrer_and_wh" in calls else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main(str(ROOT / "sample_data" / "sample_xrd.csv"))))
