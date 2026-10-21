import importlib.util
from pathlib import Path

_spec = importlib.util.spec_from_file_location("secret_scan", Path(__file__).parents[1] / "scripts" / "secret_scan.py")
secret_scan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(secret_scan)


def test_flags_env_value_and_patterns():
    fake = "abcdef0123456789abcdef0123456789"
    assert secret_scan.find_secrets(f"key = '{fake}'", [fake])
    assert secret_scan.find_secrets("Authorization: Bearer " + "x" * 30, [])
    assert secret_scan.find_secrets("https://user:" + "pass@example.com/repo.git", [])


def test_clean_text_passes():
    sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"  # file hashes are fine
    assert secret_scan.find_secrets(f"sample_001,{sha}\nheaders={{'Authorization': f'Bearer {{key}}'}}", ["not-present-secret"]) == []


def test_env_loader_reads_only_secret_vars(tmp_path):
    env = tmp_path / ".env"
    env.write_text("LLM_API_KEY=supersecretvalue123\nLLM_MODEL=gpt-oss:120b\nMP_API_KEY=\n")
    assert secret_scan.load_env_secrets(env) == ["supersecretvalue123"]
