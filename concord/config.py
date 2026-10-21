"""Configuration: non-secret settings from config.yaml, secrets from .env only."""
from functools import lru_cache
from pathlib import Path

import yaml
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]
SECRET_KEYS = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL", "MP_API_KEY", "REF_GIT_USERNAME", "REF_GIT_TOKEN", "EYE_MODULE_PATH")


@lru_cache
def settings() -> dict:
    return yaml.safe_load((ROOT / "config.yaml").read_text())


@lru_cache
def env() -> dict:
    """Values from .env only (never the process environment), empty strings dropped."""
    values = dotenv_values(ROOT / ".env")
    return {k: v for k in SECRET_KEYS if (v := (values.get(k) or "").strip())}
