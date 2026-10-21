#!/usr/bin/env python3
"""Pre-commit secret scan: block staged content that contains a .env secret or a common key pattern.

Stdlib only, so the git hook runs with any python3.
"""
import re
import subprocess
import sys
from pathlib import Path

SECRET_VARS = ("LLM_API_KEY", "MP_API_KEY", "REF_GIT_TOKEN", "REF_GIT_USERNAME", "LLM_BASE_URL")
PATTERNS = {
    "private key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "bearer token": re.compile(r"Bearer\s+[A-Za-z0-9._\-]{24,}"),
    "openai-style key": re.compile(r"\bsk-[A-Za-z0-9_\-]{20,}"),
    "github token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}"),
    "aws access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "credentials in URL": re.compile(r"https?://[^/\s:@]+:[^/\s@]+@"),
}


def load_env_secrets(env_path: Path) -> list[str]:
    if not env_path.exists():
        return []
    values = []
    for line in env_path.read_text().splitlines():
        key, sep, value = line.partition("=")
        if sep and key.strip() in SECRET_VARS and len(value.strip()) >= 8:
            values.append(value.strip())
    return values


def find_secrets(text: str, secrets: list[str]) -> list[str]:
    hits = ["value of a .env secret" for s in secrets if s in text]
    hits += [name for name, rx in PATTERNS.items() if rx.search(text)]
    return hits


def main() -> int:
    root = Path(subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip())
    secrets = load_env_secrets(root / ".env")
    staged = subprocess.check_output(["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"], text=True, cwd=root).split()
    problems = []
    for path in staged:
        if Path(path).name == ".env":
            problems.append(f"{path}: .env must never be committed")
            continue
        blob = subprocess.run(["git", "show", f":{path}"], capture_output=True, cwd=root).stdout
        if b"\0" in blob[:8000]:
            continue  # binary file
        for hit in find_secrets(blob.decode("utf-8", "replace"), secrets):
            problems.append(f"{path}: {hit}")
    if problems:
        print("secret scan: commit blocked\n  " + "\n  ".join(problems), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
