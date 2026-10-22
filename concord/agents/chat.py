"""Questions about one analysed sample, answered from its evidence bundle only.

The reply cites evidence ids and passes the number guard: a reply with a number the evidence lacks is sent back once
with the numbers named, and anything still unsupported is returned to the page to be marked, never hidden.
"""
import json
from typing import Literal

from pydantic import BaseModel, Field

from concord.agents.evidence import number_guard
from concord.llm.adk_model import shared_client

SUGGESTIONS = ("none", "run_fast", "run_full", "find_priors")

SYSTEM = """You are the analyst of Concord, which fits X-ray diffraction (XRD), the pair distribution function (PDF), EXAFS
and XANES of one nanoparticle sample and checks them against each other (C1-C7). A materials scientist asks about
this sample. Answer from the evidence JSON below only, in plain sentences (at most about 120 words, no tables, no
headings, no dashes as punctuation). Every number you write must appear in the evidence; never compute or estimate a new one. Cite the evidence
ids you used. If the evidence cannot answer, say so and suggest what would: "run_fast" re-runs the tools and checks,
"run_full" adds the visual inspection and the generator-critic loop, "find_priors" searches the literature.

Evidence:
{evidence}"""


class Reply(BaseModel):
    answer: str
    cites: list[str] = Field(description="evidence ids the answer uses")
    suggest: Literal[SUGGESTIONS] = Field(description="one follow-up action, or none")


def answer(evidence: dict, messages: list[dict]) -> dict:
    """messages: [{role: user|assistant, content}], oldest first; the last one is the question."""
    msgs = [{"role": "system", "content": SYSTEM.format(evidence=json.dumps(evidence))},
            *({"role": m["role"], "content": str(m["content"])[:2000]} for m in messages[-12:])]
    client = shared_client()
    r = client.chat("chat", msgs, schema=Reply)
    bad = number_guard(r.data.answer, evidence)
    if bad:
        msgs += [{"role": "assistant", "content": r.content},
                 {"role": "user", "content": f"These numbers are not in the evidence: {', '.join(bad)}. Rewrite the answer "
                                             "with only numbers from the evidence, or leave them out."}]
        r = client.chat("chat", msgs, schema=Reply)
        bad = number_guard(r.data.answer, evidence)
    return {"answer": r.data.answer, "cites": [c for c in r.data.cites if c in evidence], "suggest": r.data.suggest,
            "unsupported_numbers": bad, "tokens": r.prompt_tokens + r.completion_tokens}
