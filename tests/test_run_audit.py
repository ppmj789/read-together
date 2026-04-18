"""Tests for scripts/run_audit.sh (arg validation only — real audit run is E2E)."""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "run_audit.sh"


def _run(*args, timeout: int = 15):
    return subprocess.run(
        [str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
        timeout=timeout,
    )


def test_script_exists_and_executable():
    assert SCRIPT.is_file()
    assert SCRIPT.stat().st_mode & 0o111, f"{SCRIPT} must be executable"


def test_help_prints_usage_and_exits_zero():
    r = _run("--help")
    assert r.returncode == 0
    assert "Usage:" in r.stdout
    assert "<cycle-id>" in r.stdout
    assert "before --append-system-prompt" in r.stdout  # the CRITICAL arg-order note


def test_no_args_exits_2():
    r = _run()
    assert r.returncode == 2


def test_missing_project_exits_2(tmp_path):
    prompt = tmp_path / "prompt.txt"
    prompt.write_text("probe")
    r = _run("nonexistent-project", "02_design", str(prompt))
    assert r.returncode == 2
    assert "project not found" in r.stderr


def test_missing_prompt_file_exits_2(tmp_path):
    r = _run("book-mgmt-api", "02_design", str(tmp_path / "does-not-exist.txt"))
    # Either "project not found" if book-mgmt-api is absent on master, OR
    # "prompt file not found" if it exists. Either way exit 2.
    assert r.returncode == 2


def test_invalid_flag_exits_2():
    """Any unknown invocation pattern without 3 positional args must fail fast."""
    r = _run("--notafag")
    assert r.returncode == 2
