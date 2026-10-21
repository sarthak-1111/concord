"""Open fallback for the eye module: gpt-oss reads the residual features (it does not see the image) and returns the
same verdict format. If the LLM is unreachable, a rule on the same features decides."""
import json
from typing import Literal

from pydantic import BaseModel

from concord.agents.resolver import ACTIONS
from concord.llm.adk_model import shared_client
from concord.llm.client import LLMError


class Issue(BaseModel):
    region: str
    pattern: str
    likely_cause: str
    suggested_action: str


class Verdict(BaseModel):
    verdict: Literal["accept", "reject"]
    issues: list[Issue]


JUDGE = """You inspect a model fit to measured data through residual statistics computed by deterministic code (you do
not see the plot). Per region of the x axis: misfit_share is the region's share of the squared residual, rms_rel the
residual RMS relative to the data RMS, durbin_watson the Durbin-Watson statistic on independent points (2 = random
noise, below 1 = structured misfit). structured_regions lists regions with structured misfit, concentrated_regions regions
holding most of the misfit well above the other regions' level; unexplained_peaks lists
positive residual peaks of a diffraction pattern. Reject the fit when structured misfit or unexplained peaks show that
the model misses something real. For each issue name the region, the pattern, the likely physical cause for this
technique, and one suggested action from: {actions}, or "none". Use only numbers given to you. Reply with JSON."""


def rule_verdict(features: dict) -> dict:
    issues = [{"region": r, "pattern": "structured residual", "likely_cause": "model misses a feature in this region",
               "suggested_action": "none"} for r in features["structured_regions"]]
    issues += [{"region": r, "pattern": "concentrated misfit", "likely_cause": "a local feature the model lacks",
                "suggested_action": "none"} for r in features["concentrated_regions"] if r not in features["structured_regions"]]
    issues += [{"region": f"{x}", "pattern": "unexplained peak", "likely_cause": "a phase or reflection the model lacks",
                "suggested_action": "pdf_fit_candidate"} for x in features["unexplained_peaks"]]
    return {"verdict": "reject" if issues else "accept", "issues": issues, "inspector": "rules"}


def judge(technique: str, features: dict, context: dict) -> dict:
    prompt = JUDGE.replace("{actions}", ", ".join(ACTIONS))
    msg = json.dumps({"technique": technique, "context": context, "features": features}, default=str)
    try:
        r = shared_client().chat("judge", [{"role": "system", "content": prompt}, {"role": "user", "content": msg}], schema=Verdict)
        return {**r.data.model_dump(), "inspector": "gpt-oss judge"}
    except LLMError:
        return rule_verdict(features)
